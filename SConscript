#!/usr/bin/env python

# **************************************************************************
# *
# * Authors:     I. Foche Perez (ifoche@cnb.csic.es)
# *              J. Burguet Castell (jburguet@cnb.csic.es)
# *
# * Unidad de Bioinformatica of Centro Nacional de Biotecnologia, CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'ifoche@cnb.csic.es'
# *
# **************************************************************************


# First import the environment (this comes from SConstruct)
Import('env')


#  ************************************************************************
#  *                                                                      *
#  *                              Libraries                               *
#  *                                                                      *
#  ************************************************************************

# We might want to add freetype and make tcl depend on it. That would be:
# freetype = env.AddLibrary(
#     'freetype',
#     tar='freetype-2.5.3.tgz',
#     autoConfigTarget='config.mk')
# But because freetype's compilation is a pain, it's better to use whatever
# version is in the system.

tcl = env.AddLibrary(
    'tcl',
    tar='tcl8.6.1-src.tgz',
    buildDir='tcl8.6.1/unix',
    targets=['lib/libtcl8.6.so'],
    flags=['--enable-threads'],
    clean=['software/tmp/tcl8.6.1',
           'software/bin/tclsh8.6',
           Glob('software/lib/*tcl*'),
           Glob('software/lib/tdbc*'),
           'software/lib/thread2.7.0',
           'software/lib/pkgconfig/tcl.pc',
           Glob('software/include/*tcl*'),
           Glob('software/include/*tdbc*'),
           'software/man/man1/tclsh.1',
           Glob('software/man/man3/Tcl*'),
           'software/man/man3/TCL_MEM_DEBUG.3',
           'software/man/man3/Tdbc_Init.3',
           Glob('software/man/mann/*tcl*'),
           Glob('software/man/mann/Tcl*'),
           Glob('software/man/mann/*tdbc*'),
           Glob('software/share/man/mann/tdbc*')])

tk = env.AddLibrary(
    'tk',
    tar='tk8.6.1-src.tgz',
    buildDir='tk8.6.1/unix',
    targets=['lib/libtk8.6.so'],
    flags=['--enable-threads'],
    deps=[tcl],
    clean=['software/tmp/tk8.6.1',
           'software/bin/wish8.6',
           Glob('software/lib/*tk*'),
           'software/lib/pkgconfig/tk.pc',
           Glob('software/include/*tk*'),
           'software/man/man1/wish.1',
           Glob('software/man/man3/Tk*'),
           Glob('software/man/man3/*tk*'),
           Glob('software/man/mann/*tk*'),
           ])

sqlite = env.AddLibrary(
    'sqlite',
    tar='sqlite-3.6.23.tgz',
    targets=['lib/libsqlite3.so'],
    flags=['CPPFLAGS=-w',
           'CFLAGS=-DSQLITE_ENABLE_UPDATE_DELETE_LIMIT=1'],
    clean=['software/bin/sqlite3',
           Glob('software/lib/*sqlite*'),
           'software/lib/pkgconfig/sqlite3.pc',
           Glob('software/include/*sqlite*'),
           'software/share/man/man1/sqlite3.1',
           'software/share/man/mann/sqlite3.n'])

python = env.AddLibrary(
    'python',
    tar='Python-2.7.8.tgz',
    targets=['lib/libpython2.7.so', 'bin/python'],
    flags=['--enable-shared'],
    deps=[sqlite, tk],
    clean=[Glob('software/bin/*py*'),
           'software/bin/2to3',
           Glob('software/bin/easy_install*'),
           'software/bin/idle',
           Glob('software/lib/*python*'),
           Glob('software/lib/pkgconfig/*py*'),
           'software/include/python2.7',
           Glob('software/share/man/man1/python*')
           ])


#  ************************************************************************
#  *                                                                      *
#  *                           Python Modules                             *
#  *                                                                      *
#  ************************************************************************

# Helper function to include the python dependency automatically.
def addModule(*args, **kwargs):
    kwargs['deps'] = kwargs.get('deps', []) + python
    return env.AddModule(*args, **kwargs)


numpy = addModule(
    'numpy',
    tar='numpy-1.8.1.tgz')

six = addModule(
    'six',
    tar='six-1.7.3.tgz')

dateutil = addModule(
    'dateutil',
    flags=['--old-and-unmanageable'],
    tar='python-dateutil-1.5.tgz',
    deps=[six])
# The option '--old-and-unmanageable' avoids creating a single Python
# egg, and so we have a "matplotlib" directory that can be used as a
# target (because it is not passed as argument, it has the default value).

pyparsing = addModule(
    'pyparsing',
    tar='pyparsing-2.0.2.tgz')

matplotlib = addModule(
    'matplotlib',
    tar='matplotlib-1.3.1.tgz',
    flags=['--old-and-unmanageable'],
    deps=[numpy, dateutil, pyparsing])

setuptools = addModule(
    'setuptools',
    tar='setuptools-5.4.1.tgz',
    targets=['setuptools.pth'])

addModule(
    'psutil',
    tar='psutil-2.1.1.tgz',
    flags=['--old-and-unmanageable'])

addModule(
    'mpi4py',
    tar='mpi4py-1.3.1.tgz')

addModule(
    'scipy',
    tar='scipy-0.14.0.tgz',
    default=False,
    deps=[numpy, matplotlib])

addModule(
    'bibtexparser',
    tar='bibtexparser-0.5.tgz')

addModule(
    'django',
    tar='Django-1.5.5.tgz')

addModule(
    'paramiko',
    tar='paramiko-1.14.0.tgz',
    default=False)

addModule(
    'Pillow',
    tar='Pillow-2.5.1.tgz',
    targets=['PIL'],
    flags=['--old-and-unmanageable'],
    deps=[setuptools])


#  ************************************************************************
#  *                                                                      *
#  *                       External (EM) Packages                         *
#  *                                                                      *
#  ************************************************************************

env.AddPackage('xmipp',
               tar='Xmipp-3.1-src.tar.gz',
               url='http://xmipp.cnb.csic.es/Downloads/Xmipp-3.1-src.tar.gz',
               buildDir='xmipp',
               extraActions=[('xmipp.bashrc',
                             './install.sh --unattended=true --gui=false -j %s'
                              % GetOption('num_jobs'))],
               default=False)

env.AddPackage('bsoft',
               tar='bsoft1_8_8_Fedora_12.tgz',
               default=False)

env.AddPackage('ctffind',
               tar='ctffind_V3.5.tgz',
               default=False)

env.AddPackage('eman',
               tar='eman2.1beta3.linux64.tgz',
               extraActions=[('eman2.bashrc', './eman2-installer')],
               default=False)
# extraActions is a list of (target, command) to run after installation.

env.AddPackage('frealign',
               tar='frealign_v9.07.tgz',
               default=False)

env.AddPackage('relion',
               tar='relion-1.2.tgz',
               default=False)

env.AddPackage('spider',
               tar='spider-web-21.13.tgz',
               default=False)


# TODO: check if we have to use the "purge" option below:

# # Purge option
# if GetOption('purge'):
#     env.RemoveInstallation()
