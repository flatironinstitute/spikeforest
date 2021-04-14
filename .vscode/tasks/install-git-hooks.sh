#!/bin/bash

set -ex

cd .git/hooks
rm -f pre-commit
ln -s ../../devel/githooks/pre-commit pre-commit