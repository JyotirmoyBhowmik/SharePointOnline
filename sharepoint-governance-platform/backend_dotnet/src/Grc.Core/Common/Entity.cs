using System;

namespace Grc.Core.Common
{
    public abstract class Entity
    {
        public Guid Id { get; protected set; }
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
        public DateTime? UpdatedAt { get; set; }

        protected Entity()
        {
            Id = Guid.NewGuid();
        }
    }
}
