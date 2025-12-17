using System.Reflection;
using Grc.Core.Entities;
using Microsoft.EntityFrameworkCore;

namespace Grc.Infrastructure.Data
{
    public class GrcDbContext : DbContext
    {
        public GrcDbContext(DbContextOptions<GrcDbContext> options) : base(options)
        {
        }

        public DbSet<SiteCollection> SiteCollections { get; set; }
        public DbSet<AuditLog> AuditLogs { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);
            
            // Apply configurations from this assembly
            modelBuilder.ApplyConfigurationsFromAssembly(Assembly.GetExecutingAssembly());
        }
    }
}
