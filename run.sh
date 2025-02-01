#!/bin/bash
export MATRIX_USER="@user:matrix.org"
export MATRIX_ACCESS_TOKEN="lotOfCharactersHere" 
export MATRIX_SERVER="https://matrix.org"
# export JOIN_ON_INVITE="True"
export BOT_OWNERS="@owner:matrix.org"
poetry run hemppa
