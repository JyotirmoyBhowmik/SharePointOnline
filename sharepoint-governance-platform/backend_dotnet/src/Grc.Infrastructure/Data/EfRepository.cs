using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Threading.Tasks;
using Grc.Core.Common;
using Grc.Core.Interfaces;
using Microsoft.EntityFrameworkCore;

namespace Grc.Infrastructure.Data
{
    public class EfRepository<T> : IRepository<T> where T : Entity
    {
        protected readonly GrcDbContext _dbContext;

        public EfRepository(GrcDbContext dbContext)
        {
            _dbContext = dbContext;
        }

        public virtual async Task<T> GetByIdAsync(Guid id)
        {
            return await _dbContext.Set<T>().FindAsync(id);
        }

        public async Task<IReadOnlyList<T>> ListAllAsync()
        {
            return await _dbContext.Set<T>().ToListAsync();
        }

        public async Task<T> AddAsync(T entity)
        {
            await _dbContext.Set<T>().AddAsync(entity);
            await _dbContext.SaveChangesAsync();

            return entity;
        }

        public async Task UpdateAsync(T entity)
        {
            _dbContext.Entry(entity).State = EntityState.Modified;
            await _dbContext.SaveChangesAsync();
        }

        public async Task DeleteAsync(T entity)
        {
            _dbContext.Set<T>().Remove(entity);
            await _dbContext.SaveChangesAsync();
        }

        public async Task<int> CountAsync(ISpecification<T> spec)
        {
            return await ApplySpecification(spec).CountAsync();
        }

        public async Task<IReadOnlyList<T>> ListAsync(ISpecification<T> spec)
        {
            return await ApplySpecification(spec).ToListAsync();
        }

        private IQueryable<T> ApplySpecification(ISpecification<T> spec)
        {
             var query = _dbContext.Set<T>().AsQueryable();
             if (spec.Criteria != null)
             {
                 query = query.Where(spec.Criteria);
             }
             // Naive implementation of Includes
             foreach (var include in spec.Includes)
             {
                 query = query.Include(include);
             }
             if (spec.OrderBy != null)
             {
                 query = query.OrderBy(spec.OrderBy);
             }
             else if (spec.OrderByDescending != null)
             {
                 query = query.OrderByDescending(spec.OrderByDescending);
             }
             return query;
        }
    }
}
