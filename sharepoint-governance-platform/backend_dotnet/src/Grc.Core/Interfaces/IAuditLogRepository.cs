using System.Threading.Tasks;
using Grc.Core.Entities;

namespace Grc.Core.Interfaces
{
    public interface IAuditLogRepository : IRepository<AuditLog>
    {
        // Add specific methods for high-volume ingestion if generic repo is too slow (e.g. BulkInsert)
        Task BulkInsertAsync(IEnumerable<AuditLog> auditLogs);
    }
}
