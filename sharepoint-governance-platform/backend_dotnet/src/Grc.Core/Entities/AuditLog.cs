using System;
using System.Text.Json;
using Grc.Core.Common;

namespace Grc.Core.Entities
{
    public class AuditLog : Entity
    {
        public Guid ContentId { get; private set; } // From O365 API
        public DateTime CreationTime { get; private set; }
        public string Operation { get; private set; } // e.g. FileAccessed
        public string Workload { get; private set; } // OneDrive, SharePoint
        public string UserId { get; private set; } // UPN or ObjectId
        public string ClientIP { get; private set; }
        
        // This will be mapped to jsonb in PostgreSQL
        public string AuditDataJson { get; private set; }

        private AuditLog() { }

        public AuditLog(Guid contentId, DateTime creationTime, string operation, string workload, string userId, string clientIp, string auditDataJson)
        {
            ContentId = contentId;
            CreationTime = creationTime;
            Operation = operation;
            Workload = workload;
            UserId = userId;
            ClientIP = clientIp;
            AuditDataJson = auditDataJson;
        }
    }
}
