using System.Threading.Tasks;
using Grc.Core.Entities;

namespace Grc.Core.Interfaces
{
    public interface ISiteRepository : IRepository<SiteCollection>
    {
        Task<SiteCollection> GetByUrlAsync(string url);
        Task<bool> ExistsAsync(string url);
    }
}
