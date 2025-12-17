using System.Threading.Tasks;
using Grc.Core.Entities;
using Grc.Core.Interfaces;
using Microsoft.EntityFrameworkCore;

namespace Grc.Infrastructure.Data
{
    public class SiteRepository : EfRepository<SiteCollection>, ISiteRepository
    {
        public SiteRepository(GrcDbContext dbContext) : base(dbContext)
        {
        }

        public async Task<SiteCollection> GetByUrlAsync(string url)
        {
            return await _dbContext.SiteCollections
                .FirstOrDefaultAsync(x => x.Url == url);
        }

        public async Task<bool> ExistsAsync(string url)
        {
            return await _dbContext.SiteCollections
                .AnyAsync(x => x.Url == url);
        }
    }
}
