#!/bin/bash
set -e
DOTNET=$(pwd)/.dotnet/dotnet

cd backend_dotnet
$DOTNET build
echo "Build successful."
