using Grc.Core.Interfaces;
using Grc.Infrastructure.Data;
using MassTransit;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace Grc.Infrastructure
{
    public static class DependencyInjection
    {
        public static IServiceCollection AddInfrastructureServices(this IServiceCollection services, IConfiguration configuration)
        {
            // Persistence
            services.AddDbContext<GrcDbContext>(options =>
                options.UseNpgsql(
                    configuration.GetConnectionString("DefaultConnection"),
                    b => b.MigrationsAssembly(typeof(GrcDbContext).Assembly.FullName)));

            services.AddScoped(typeof(IRepository<>), typeof(EfRepository<>));
            services.AddScoped<ISiteRepository, SiteRepository>();
            services.AddScoped<IAuditLogRepository, AuditLogRepository>();

            // Messaging (MassTransit)
            services.AddMassTransit(x =>
            {
                x.SetKebabCaseEndpointNameFormatter();

                // Consumers will be added here or in the Worker project
                
                x.UsingRabbitMq((context, cfg) =>
                {
                    cfg.Host(configuration["RabbitMq:Host"], "/", h =>
                    {
                        h.Username(configuration["RabbitMq:Username"]);
                        h.Password(configuration["RabbitMq:Password"]);
                    });

                    cfg.ConfigureEndpoints(context);
                });
            });

            return services;
        }
    }
}
