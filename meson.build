project('gst',
  version: run_command(
    'grep',
    'APP_VERSION',
    files('gst/conf.py')
  ).stdout().split(' = ')[1].strip().strip('"'),
  meson_version: '>= 0.45.1'
)
# project version is defined in gst/conf.py

# Importing modules
# i18n = import('i18n')
python3 = import('python3')
python = import('python3')

prefix = get_option('prefix')
PKGDATA_DIR = join_paths(prefix, get_option('datadir'), meson.project_name())
DATA_DIR = PKGDATA_DIR
PYTHON_DIR = join_paths(prefix, python.sysconfig_path('purelib'))

message('Looking for dependencies')
python_bin = python.find_python()
if not python_bin.found()
    error('No valid python3 binary found')
else
    message('Found python3 binary')
endif

# Dependencies
dependency('gobject-introspection-1.0', version: '>= 1.56.0')

install_subdir('gst', install_dir: PYTHON_DIR)
subdir('data')
subdir('bin')

meson.add_install_script('scripts/meson_post_install.py')