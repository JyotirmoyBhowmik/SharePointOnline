#!/bin/bash
set -e
DOTNET=$(pwd)/.dotnet/dotnet

# Create directory structure
mkdir -p backend_dotnet/src
cd backend_dotnet

# Create Solution
$DOTNET new sln -n Grc

# Create Projects
cd src
$DOTNET new classlib -n Grc.Core
$DOTNET new classlib -n Grc.Infrastructure
$DOTNET new webapi -n Grc.Api
$DOTNET new worker -n Grc.Worker
$DOTNET new classlib -n Grc.Workflows

# Go back to solution root
cd ..

# Add projects to solution
$DOTNET sln add src/Grc.Core/Grc.Core.csproj
$DOTNET sln add src/Grc.Infrastructure/Grc.Infrastructure.csproj
$DOTNET sln add src/Grc.Api/Grc.Api.csproj
$DOTNET sln add src/Grc.Worker/Grc.Worker.csproj
$DOTNET sln add src/Grc.Workflows/Grc.Workflows.csproj

# Add Project References
# Infrastructure depends on Core
$DOTNET add src/Grc.Infrastructure reference src/Grc.Core

# Api depends on Infrastructure and Workflows
$DOTNET add src/Grc.Api reference src/Grc.Infrastructure
$DOTNET add src/Grc.Api reference src/Grc.Workflows

# Worker depends on Infrastructure
$DOTNET add src/Grc.Worker reference src/Grc.Infrastructure

# Workflows depends on Core
$DOTNET add src/Grc.Workflows reference src/Grc.Core

echo "Scaffolding complete."
