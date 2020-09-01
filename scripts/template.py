import argparse
import datetime
import importlib
import json
import os
import pprint
import subprocess
import sys

from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateError, TemplateSyntaxError

from os.path import realpath, dirname, join

_date_fmt = '%A, %B %d, %Y'
_time_fmt = '%I:%M %p'
_datetime_fmt = '{} at {}'.format(_date_fmt, _time_fmt)

root = dirname(dirname(realpath(__file__)))


class FormattedDateTime(datetime.datetime):
    def __str__(self):
        return self.strftime(_datetime_fmt)


class FormattedDate(datetime.datetime):
    def __str__(self):
        return self.strftime(_date_fmt)


class FormattedTime(datetime.datetime):
    def __str__(self):
        return self.strftime(_time_fmt)


def get_creation(infile):
    get_creation = subprocess.Popen(
        [join(root, "scripts", "get_creation.sh"), infile],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True
    )

    out, errs = get_creation.communicate()
    if errs:
        print(errs)
    return int(out)


def getMetadata(infile: str, metadata: str, verbose=False, dryrun=False
                ) -> dict:
    """
    Get the metadata for the given file

    :param str infile:
    :param str metadata:
    :param bool verbose:
    """

    inname = os.path.basename(infile)

    metafile = os.path.join(os.path.dirname(infile), metadata)

    metadata = dict()
    if os.path.exists(metafile):
        with open(metafile) as f:
            metadata = json.load(f)

    data = metadata.get(inname, dict())

    if not data.get('created'):
        if verbose:
            print("getting creation date of %s" % infile)
        data['created'] = get_creation(infile)
        if verbose:
            print("Creation date of %s is estimated to be %s" % (
                infile, FormattedDateTime.fromtimestamp(data['created'])
            ))

    if data != metadata.get(inname):
        if verbose:
            print("Updating metadata '%s' for '%s'" % (metafile, infile))
        metadata[inname] = data
        with open(metafile, 'w') as f:
            json.dump(metadata, f)

    # Populate the metadata with values that don't need to be saved

    data['date'] = FormattedDate.fromtimestamp(
        data['created']
    )
    data['created'] = FormattedDateTime.fromtimestamp(
        data['created']
    )

    data['modified'] = FormattedDateTime.fromtimestamp(
        os.path.getmtime(infile)
    )

    data['rendered'] = FormattedDateTime.now()

    data['name'] = os.path.splitext(inname)[0]

    return data


class DependencyLoader(FileSystemLoader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dependencies = set()
    
    def get_source(self, environment, template):
        contents, filename, uptodate = super().get_source(environment, template)
        self.dependencies.add(filename)
        return contents, filename, uptodate
    
    def add_dependency(self, path):
        self.dependencies.add(path)


def write_dependencies(depFile, dep, requirements):
    if not os.path.exists(dirname(depFile)):
        os.makedirs(dirname(depFile))
    
    with open(depFile, "w") as f:
        f.write("{}: \\\n".format(dep))
        f.write(" \\\n".join(["  %s" % i for i in requirements]))
        f.write("\n")


def main(infile, outfile, metadata, variables: dict = None, verbose=False,
         dryrun=False, **kwargs):
    """
    Render a template

    :param str infile:
    :param str outfile:
    :param str metadata:
    :param dict variables:
    :param bool verbose:
    :param bool dryrun:
    """
    indir = os.path.dirname(infile)
    inname = os.path.basename(infile)
    data = getMetadata(infile, metadata, verbose, dryrun)

    loader = DependencyLoader(
        [indir, os.path.join(indir, 'templates'), 'templates']
    )

    def import_module(module_name):
        """
        Import a module, and return it as a variable
        """
        if os.path.abspath(indir) not in sys.path:
            sys.path.append(os.path.abspath(indir))
        path = join(os.path.abspath(indir), module_name)
        loader.add_dependency(path)
        return importlib.import_module(module_name)


    def read_file(file_name):
        """
        Read and return the contents of a file
        """
        if os.path.isabs(file_name):
            path = file_name
        else:
            path = join(indir, file_name)

        loader.add_dependency(path)
        with open(path) as f:
            return f.read()

    data['import_module'] = import_module
    data['read_file'] = read_file

    env = Environment(loader=loader)

    env.globals.update(data)

    try:
        template = env.get_template(inname)

        variables = variables or dict()
        rendered = template.render(**variables) + '\n'
    except TemplateSyntaxError as e:
        print("There was an error while parsing %s@%d:\n\n\t%s\n%s" % (
            e.filename, e.lineno, e.source, str(e)
        ))
        sys.exit(1)
    except TemplateError as e:
        print("%s: %s" % (type(e).__name__, e))
        sys.exit(1)
    
    if not dryrun:
        if not os.path.isdir(dirname(outfile)):
            os.makedirs(dirname(outfile))
        with open(outfile, 'w') as f:
            f.write(rendered)
    
    return loader.dependencies


def parseArgs(args: list = None):
    """
    Parse the command line arguments

    :param list args:

    :return namespace: parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Render the templates"
    )

    parser.add_argument(
        "-v", "--verbose", dest="verbose", action="store_true", default=False,
        help="Print more verbose output"
    )
    parser.add_argument(
        "-n", "--dry-run", dest="dryrun", action="store_true", default=False,
        help="Don't perform any changes"
    )

    parser.add_argument(
        "infile", help="In file"
    )
    parser.add_argument(
        "-out", dest="outfile", default=None, metavar="FILE",
        help="Outfile (default: [input]-render.[ext])"
    )
    parser.add_argument(
        "-meta", dest="metadata", default=".metadata.json", metavar="FILE",
        help="Metafile name (default: .metadata.json)"
    )
    parser.add_argument(
        "-dep", dest="dependency", default=None, metavar="FILE", nargs=2,
        help="Create a depenency file for MakeFiles"
    )
    var = parser.add_argument_group("Variables")
    m_var = var.add_mutually_exclusive_group()
    m_var.add_argument(
        "-var", nargs=2, dest="variables", action='append', default=list(),
        metavar=("KEY", "VALUE"),
        help="set a template variable"
    )
    m_var.add_argument(
        "-varfile", dest="variable_file", default=None, metavar="FILE",
        help=("set the variables from a python file (all the locals from "
              "that file will be used as variables)")
    )

    kwargs = parser.parse_args(args)

    if kwargs.variable_file:
        # Import given module file
        var_dir = os.path.dirname(kwargs.variable_file)
        if var_dir not in sys.path:
            sys.path.append(var_dir)
        mod = os.path.basename(kwargs.variable_file).replace('.py', '')
        module = importlib.import_module(mod)
        # Get the variables from that module
        kwargs.variables = dict(
            (k, v) for k, v in vars(module).items()
            if not k.startswith('__')
        )
    else:
        for var in kwargs.variables:
            try:
                vl = dict()
                exec('v = ' + var[1], globals(), vl)
                var[1] = vl['v']
            except Exception:
                pass
        kwargs.variables = dict(kwargs.variables)
    del kwargs.variable_file

    if not kwargs.outfile:
        outname = os.path.splitext(os.path.basename(kwargs.infile))
        kwargs.outfile = os.path.join(
            os.path.dirname(kwargs.infile),
            '%s-render%s' % outname
        )

    if kwargs.verbose:
        pprint.pprint(vars(kwargs))

    return kwargs


if __name__ == "__main__":
    kwargs = parseArgs()
    dependencies = main(**vars(kwargs))
    if kwargs.verbose:
        print("dependencies: %s" % dependencies)
    if not kwargs.dryrun and kwargs.dependency is not None:
        write_dependencies(kwargs.dependency[0], kwargs.dependency[1], dependencies)
