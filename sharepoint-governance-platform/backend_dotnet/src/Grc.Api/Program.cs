using Grc.Infrastructure;
using Grc.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Clean Architecture: Add Infrastructure Layer
builder.Services.AddInfrastructureServices(builder.Configuration);

// Add Workflows (Elsa) - To be implemented later fully
// builder.Services.AddElsa(...);

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

app.UseAuthorization();

app.MapControllers();

// Auto-migrate Database on startup (for development convenience)
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<GrcDbContext>();
    // db.Database.Migrate(); // Commented out until we have migrations
}

app.Run();
