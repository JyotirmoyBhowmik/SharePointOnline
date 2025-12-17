using Grc.Core.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Grc.Infrastructure.Data.Config
{
    public class AuditLogConfiguration : IEntityTypeConfiguration<AuditLog>
    {
        public void Configure(EntityTypeBuilder<AuditLog> builder)
        {
            builder.HasKey(x => x.Id);
            
            // Partitioning logic would eventually go here if using raw SQL migration for creating partition table

            builder.Property(x => x.Workload).HasMaxLength(50);
            builder.Property(x => x.Operation).HasMaxLength(100);
            builder.Property(x => x.UserId).HasMaxLength(256);
            
            builder.HasIndex(x => x.CreationTime);
            builder.HasIndex(x => x.Workload);

            // POSTGRES SPECIFIC: JSONB Mapping
            builder.Property(x => x.AuditDataJson)
                .HasColumnType("jsonb");
        }
    }
}
