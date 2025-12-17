using Grc.Core.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Grc.Infrastructure.Data.Config
{
    public class SiteConfiguration : IEntityTypeConfiguration<SiteCollection>
    {
        public void Configure(EntityTypeBuilder<SiteCollection> builder)
        {
            builder.HasKey(x => x.Id);

            builder.Property(x => x.Url)
                .IsRequired()
                .HasMaxLength(2048);
            
            builder.HasIndex(x => x.Url)
                .IsUnique();

            builder.Property(x => x.Title)
                .HasMaxLength(500);

            builder.Property(x => x.Template)
                .HasMaxLength(100);

            builder.Property(x => x.SharingCapability)
                .HasMaxLength(50);
                
            builder.Ignore(x => x.IsDeleted); // Example: if soft delete is handled by global query filter or distinct logic
             // Actually, the requirements mentioned "Zombie" sites being marked as deleted, implying persistence.
             // So I should map it.
             builder.Property(x => x.IsDeleted).IsRequired();
        }
    }
}
