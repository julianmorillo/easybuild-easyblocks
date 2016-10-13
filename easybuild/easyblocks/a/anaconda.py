##
# Copyright 2009-2016 Ghent University
#
# This file is part of EasyBuild,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://www.vscentrum.be),
# Flemish Research Foundation (FWO) (http://www.fwo.be/en)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# http://github.com/hpcugent/easybuild
#
# EasyBuild is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation v2.
#
# EasyBuild is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EasyBuild.  If not, see <http://www.gnu.org/licenses/>.
##
"""
EasyBuild support for building and installing Anaconda, implemented as an easyblock

@author: Jillian Rowe (New York University Abu Dhabi)
"""

import shutil
import os
import stat

import easybuild.tools.environment as env
from easybuild.framework.easyconfig import CUSTOM
from easybuild.easyblocks.generic.binary import Binary
from easybuild.tools.run import run_cmd
from easybuild.tools.build_log import EasyBuildError
from easybuild.tools.filetools import adjust_permissions, rmtree2


def set_conda_env(installdir):
    """ Set the correct environmental variables for conda """
    myEnv = os.environ.copy()
    env.setvar('PATH', "{}/bin".format(installdir) + ":" + myEnv["PATH"])
    env.setvar('CONDA_ENV', installdir)
    env.setvar('CONDA_DEFAULT_ENV', installdir)


def pre_install_step(log, pre_install_cmd = None):
    """ User defined pre install step """
    if not pre_install_cmd:
        pass
    else:
        log.debug('Pre command run', pre_install_cmd)
        run_cmd(pre_install_cmd, log_all=True, simple=True)
        log.info('Pre command run {}'.format(pre_install_cmd))


def post_install_step(log, installdir, post_install_cmd):
    """ User defined post install step """
    if not post_install_cmd:
        pass
    else:
        log.debug('Post command run', post_install_cmd)
        set_conda_env(installdir)
        run_cmd(post_install_cmd, log_all=True, simple=True)
        log.info('Post command run {}'.format(post_install_cmd))


def initialize_conda_env(installdir):
    """ Initialize the conda env """
    rmtree2(installdir)
    cmd = "conda config --add create_default_packages setuptools"
    run_cmd(cmd, log_all=True, simple=True)


class EB_Anaconda(Binary):
    """Support for building/installing Anaconda."""

    @staticmethod
    def extra_options(extra_vars=None):
        """Extra easyconfig parameters specific to Anaconda."""
        extra_vars = Binary.extra_options(extra_vars)
        extra_vars.update({
            'pre_install_cmd': [None, "Commands before install: setting custom environmental variables, etc", CUSTOM],
            'post_install_cmd': [None, "Commands after install: pip install, cpanm install, etc", CUSTOM],
        })
        return extra_vars

    def install_step(self):
        """Copy all files in build directory to the install directory"""

        pre_install_step(self.log, self.cfg['pre_install_cmd'])

        rmtree2(self.installdir)
        install_script = self.src[0]['name']

        adjust_permissions(os.path.join(self.builddir, install_script), stat.S_IRUSR|stat.S_IXUSR)

        cmd = "./%s -p %s -b -f" % (install_script, self.installdir)
        self.log.info("Installing %s using command '%s'..." % (self.name, cmd))
        run_cmd(cmd, log_all=True, simple=True)

        post_install_step(self.log, self.installdir, self.cfg['post_install_cmd'])

    def make_module_req_guess(self):
        """
        A dictionary of possible directories to look for.
        """
        return {
            'MANPATH': ['man', os.path.join('share', 'man')],
            'PATH': ['bin', 'sbin'],
            'PKG_CONFIG_PATH': [os.path.join(x, 'pkgconfig') for x in ['lib', 'lib32', 'lib64', 'share']],
        }

    def sanity_check_step(self):
        """
        Custom sanity check for Anaconda
        """
        bins = ['2to3', 'activate', 'conda', 'deactivate', 'ipython', 'pydoc', 'python', 'sqlite3']
        custom_paths = {
            'files': [os.path.join('bin', x) for x in bins],
            'dirs': ['bin', 'etc', 'lib', 'pkgs'],
        }
        super(EB_Anaconda, self).sanity_check_step(custom_paths=custom_paths)
