#!/bin/bash

# cde dummy package build script

VERSION_STRING="0.2-alfa"
PACKAGE_BASE_NAME="cde_dummy"

# Take the start location as the Collector root source dir
SOURCE_DIR=`pwd`

#Check build dir location
if [ -z $CDE_CLI_BUILDDIR ]; then
  CDE_CLI_BUILDDIR="$HOME/BUILD"
fi
mkdir -p $CDE_CLI_BUILDDIR
if [ $? -ne 0 ]; then
  echo "Failed creating build dir. Exiting."
  exit 1
fi

cd $CDE_CLI_BUILDDIR
rm -f $PACKAGE_NAME".zip"

BASE_DIR="dummy"
mkdir -p $BASE_DIR
# Cleanup the existing, if any
cd $BASE_DIR
rm -rf bin
rm -rf scpt
rm -f README module.info

# Make the dirs
mkdir bin
mkdir scpt

# Copy the executables
cd bin
cp $SOURCE_DIR/dummy.py .
cp $SOURCE_DIR/dummyd.py .

# Copy the script files
cd ../scpt
cp $SOURCE_DIR/post_inst.py .
cp $SOURCE_DIR/post_uninst.py .

# Copy the base doc
cd ..
cp $SOURCE_DIR/README .
cp $SOURCE_DIR/module.info .

# Make the compressed package
cd ..
PACKAGE_NAME=$PACKAGE_BASE_NAME"-"$VERSION_STRING
zip -r $PACKAGE_NAME".zip" $BASE_DIR

cd $SOURCE_DIR
echo "$PACKAGE_NAME package created."

