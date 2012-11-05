#!/bin/bash
# Relinux runner script
# Author: Joel Leclerc (MiJyn) <lkjoel@ubuntu.com>
# Part of the relinux toolkit

# Global variables
export TRUE=0
export FALSE=1
export RELINUXCONFDIR=MAKEFILE_ENTER_CONF_DIR
export RELINUXLIBDIR=MAKEFILE_ENTER_LIB_DIR
export RELINUXEXECFILE=$RELINUXLIBDIR/relinux/__main__.py
if [[ "$RELINUXCONFDIR" == "MAKE""FILE_ENTER_CONF_DIR" || \
"$RELINUXLIBDIR" == "MAKE""FILE_ENTER_LIB_DIR" ]]
then
	echo "You need to run 'make' (without quotes) to generate this executable"
	exit 1
fi
if [ ! -d $RELINUXLIBDIR -o ! -f $RELINUXEXECFILE ]
then
	echo "Relinux was not properly installed. Try reinstalling"
	exit 1
fi

function get_pyver() {
	PYVER=`$PYEXEC -c 'import sys; print(sys.version_info[0])'`
	echo $PYVER
}

export PYEXEC=/usr/bin/python
export GIVEUP=$FALSE
if [ `get_pyver` -gt 2 ]
then
	# Try to find a python2 executable
	PYEXEC1=`ls /usr/bin/python2* | grep -E '/usr/bin/python2[^a-zA-Z]*$' | sort -V | tail -1`
	if [ ! -z $PYEXEC1 ]
	then
		PYEXEC=$PYEXEC1
	fi
	if [ `get_pyver` -gt 2 ]
	then
		# Give up
		GIVEUP=$TRUE
	fi
fi
if [ $GIVEUP -eq $TRUE ]
then
	echo "Warning: Python 3 is being used. Relinux might have unexpected behavior because of this"
fi

$PYEXEC $RELINUXEXECFILE