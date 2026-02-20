# Cost Estimation

## Monthly Cost Breakdown

This estimation is for light to moderate usage (~100-500 documents/month).

| Resource | SKU/Tier | Estimated Monthly Cost |
|----------|----------|----------------------|
| **Azure Functions** | Consumption (Y1) | $0 - $5 |
| **Storage Account** | Standard LRS | $1 - $5 |
| **Static Web App** | Free | $0 |
| **Key Vault** | Standard | $0.03/10k operations |
| **Event Grid** | Basic | $0.60/million operations |
| **Application Insights** | Pay-as-you-go | $2 - $10 |
| **Azure AI Foundry (Mistral)** | Pay-per-use | $5 - $50 |

### **Total Estimated: $10 - $75/month**

## Detailed Breakdown

### Azure Functions (Consumption Plan)

- **Free grant**: 1 million requests/month, 400,000 GB-s
- **After free tier**: $0.20 per million executions
- **Compute**: $0.000016/GB-s

For 500 documents/month (assuming 30s average processing time):
- Executions: 500 × 2 (blob + HTTP) = 1,000 (within free tier)
- Compute: 500 × 30s × 1.5GB = 22,500 GB-s (within free tier)

**Cost: ~$0-5/month**

### Storage Account

- **Blob storage**: $0.0184/GB/month (Hot tier)
- **Operations**: $0.005/10,000 operations

For 500 documents (~5MB each):
- Storage: 500 × 5MB × 4 formats = 10GB = $0.18
- Operations: ~10,000 = $0.005

**Cost: ~$1-5/month**

### Azure AI Foundry (Mistral OCR)

Pricing varies by model and region. Typical rates:
- **Per page**: $0.01 - $0.05
- **Per 1000 tokens**: Varies

For 500 documents (average 3 pages each):
- Pages: 500 × 3 = 1,500 pages
- Cost: 1,500 × $0.02 = $30

**Cost: ~$5-50/month** (depends on document complexity)

### Application Insights

- **Data ingestion**: $2.30/GB
- **Retention**: First 90 days free

For moderate logging:
- ~1-5 GB/month of logs

**Cost: ~$2-10/month**

## Scaling Costs

### High Volume (5,000+ documents/month)

| Resource | Estimated Monthly Cost |
|----------|----------------------|
| Azure Functions | $10 - $30 |
| Storage Account | $10 - $30 |
| Azure AI Foundry | $150 - $500 |
| Application Insights | $20 - $50 |
| **Total** | **$200 - $600/month** |

### Enterprise (50,000+ documents/month)

Consider:
- **Premium Functions Plan**: Better performance, VNET integration
- **Reserved capacity**: Discounts for committed usage
- **Blob storage tiers**: Cool/Archive for processed documents

## Cost Optimization Tips

### 1. Use Consumption Plan
Start with consumption plan - only pay for what you use.

### 2. Optimize Storage
- Move processed documents to Cool tier after 30 days
- Delete old extractions after retention period
- Use lifecycle management policies

### 3. Batch Processing
- Process multiple documents in single function execution
- Reduces per-execution overhead

### 4. Monitor and Alert
- Set up cost alerts at $50, $100, $200 thresholds
- Review Application Insights for optimization opportunities

### 5. Right-size AI Usage
- Only process documents that need OCR
- Skip text-based PDFs (use direct text extraction)
- Cache results to avoid reprocessing

## Azure Cost Calculator

Use the [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/) for custom estimates:

1. Add resources from this architecture
2. Adjust quantities based on expected usage
3. Compare regions for cost differences
4. Apply any enterprise agreements or reservations

## Free Tier Maximization

For portfolio/demo purposes, stay within free tiers:
- Functions: 1M requests/month free
- Storage: 5GB free (in some subscriptions)
- Static Web Apps: Free tier available
- Application Insights: 5GB/month free

**Minimal demo cost: ~$5-15/month** (primarily Mistral API usage)
