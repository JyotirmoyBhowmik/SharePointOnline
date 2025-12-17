using System;
using Grc.Core.Common;

namespace Grc.Core.Entities
{
    public class SiteCollection : Entity
    {
        public string Url { get; private set; }
        public string Title { get; private set; }
        public string Template { get; private set; } // e.g. SITEPAGEPUBLISHING#0
        public Guid TenantId { get; private set; }
        
        public long StorageUsed { get; private set; }
        public long StorageQuota { get; private set; }
        public bool IsHubSite { get; private set; }
        public string SharingCapability { get; private set; } // ExternalUserSharingOnly, etc.
        
        public DateTime? LastClassified { get; set; }
        public DateTime? LastReviewed { get; set; }
        
        public bool IsDormant { get; set; }
        public bool IsDeleted { get; set; }

        private SiteCollection() { } // EF Core

        public SiteCollection(string url, string title, Guid tenantId)
        {
            if (string.IsNullOrWhiteSpace(url)) throw new ArgumentNullException(nameof(url));
            Url = url;
            Title = title;
            TenantId = tenantId;
        }

        public void UpdateStats(long storageUsed, long storageQuota, bool isHubSite, string sharingCapability)
        {
            StorageUsed = storageUsed;
            StorageQuota = storageQuota;
            IsHubSite = isHubSite;
            SharingCapability = sharingCapability;
            UpdatedAt = DateTime.UtcNow;
        }
        
        public void MarkAsDormant()
        {
            IsDormant = true;
            UpdatedAt = DateTime.UtcNow;
        }

        public void MarkReviewed()
        {
            LastReviewed = DateTime.UtcNow;
        }
    }
}
