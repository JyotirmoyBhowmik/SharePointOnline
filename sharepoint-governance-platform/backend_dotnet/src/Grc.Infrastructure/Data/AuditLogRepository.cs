using System.Collections.Generic;
using System.Threading.Tasks;
using Grc.Core.Entities;
using Grc.Core.Interfaces;
using Npgsql;

namespace Grc.Infrastructure.Data
{
    public class AuditLogRepository : EfRepository<AuditLog>, IAuditLogRepository
    {
        public AuditLogRepository(GrcDbContext dbContext) : base(dbContext)
        {
        }

        public async Task BulkInsertAsync(IEnumerable<AuditLog> auditLogs)
        {
            // For high performance, we should use Npgsql Binary Importer (COPY)
            // But getting the NpgsqlConnection from EF Core requires some casting.
            // Simplified version using EF Core AddRange for now, but leaving comment for optimization.
            
            await _dbContext.AuditLogs.AddRangeAsync(auditLogs);
            await _dbContext.SaveChangesAsync();
        }
    }
}
