#!/bin/bash
set -e
DOTNET=$(pwd)/.dotnet/dotnet

echo "Installing packages for Grc.Infrastructure..."
cd backend_dotnet/src/Grc.Infrastructure
$DOTNET add package Npgsql.EntityFrameworkCore.PostgreSQL --version 8.0.0
$DOTNET add package Microsoft.EntityFrameworkCore.Design --version 8.0.0
$DOTNET add package MassTransit.RabbitMQ
$DOTNET add package Microsoft.Graph
$DOTNET add package PnP.Core

echo "Installing packages for Grc.Api..."
cd ../Grc.Api
$DOTNET add package Microsoft.EntityFrameworkCore.Design --version 8.0.0
$DOTNET add package Swashbuckle.AspNetCore
$DOTNET add package Elsa
$DOTNET add package Elsa.Http
# $DOTNET add package Elsa.Activities.Http

echo "Installing packages for Grc.Worker..."
cd ../Grc.Worker
$DOTNET add package MassTransit.RabbitMQ
$DOTNET add package Microsoft.Extensions.Hosting

echo "Installing packages for Grc.Workflows..."
cd ../Grc.Workflows
$DOTNET add package Elsa

echo "Package installation complete."
