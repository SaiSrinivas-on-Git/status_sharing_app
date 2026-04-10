# Cost Optimization

## Firebase Free Tier (Spark Plan)

| Service | Free Tier | Your Expected Usage |
|---------|-----------|-------------------|
| Authentication | Unlimited | ✅ Well within |
| Firestore reads | 50,000/day | ~100/day → ✅ |
| Firestore writes | 20,000/day | ~50/day → ✅ |
| Firestore storage | 1 GB | < 1 MB → ✅ |
| Cloud Messaging | Unlimited | ✅ |
| Hosting | 10 GB/month | < 100 MB → ✅ |

## Cloud Run (Free Tier)

| Resource | Free Tier | Your Expected Usage |
|----------|-----------|-------------------|
| Requests | 2 million/month | ~1,000/month → ✅ |
| CPU | 180,000 vCPU-seconds/month | Minimal → ✅ |
| Memory | 360,000 GiB-seconds/month | Minimal → ✅ |

### Key: Scale to Zero

Cloud Run is configured with `min-instances=0`, meaning **you pay nothing when no one is using it**. The first request after idle may take 2-3 seconds (cold start), but subsequent requests are fast.

## Google Maps APIs

| API | Free Tier | Usage Strategy |
|-----|-----------|---------------|
| Geocoding | $200/month credit (~40,000 calls) | Rate-limited to 10/min, cached 5 min |
| Roads | $200/month credit (~10,000 calls) | Only called when location changes |

### Cost Mitigation

1. **Caching**: Results cached for 5 minutes by location grid (~100m)
2. **Rate limiting**: Max 10 API calls per minute
3. **Conditional calls**: Only called when device reports movement or significant location change
4. **Optional**: Set a billing budget alert at $5/month

## Cost Summary

For typical personal use (a few viewers checking status a few times per day):

| Service | Monthly Cost |
|---------|-------------|
| Firebase | **$0** (Spark plan) |
| Cloud Run | **$0** (within free tier) |
| Google Maps (optional) | **$0** (within $200 credit) |
| **Total** | **$0/month** |

## Future Considerations

If usage grows significantly:
- **Firestore**: Upgrade to Blaze plan ($0.06/100K reads, $0.18/100K writes)
- **Cloud Run**: Costs only if you exceed free tier
- **Maps**: Disable outdoor heuristic to eliminate this cost entirely
