# Sidequest Tasks - Post Bedrock Implementation
# Generated: 2025-09-25
# Priority: Lower than current bedrock architecture completion

## Individual Items Enhancement Tasks
**Priority: Medium**
- **Task**: Enhance unified_api_client.get_item_master() to support common_name filtering
- **Issue**: Individual RFID items expansion returns empty results because API doesn't filter by equipment name
- **Impact**: Users can't drill down to see specific RFID tagged items
- **Estimated Effort**: 2-3 hours
- **Dependencies**: Current bedrock architecture working

## URL Encoding Fix
**Priority: Low**
- **Task**: Fix double URL encoding in frontend JavaScript
- **Issue**: `Rectangle%2520Linen` instead of `Rectangle%20Linen` in browser logs
- **Impact**: Cosmetic, doesn't break functionality
- **Estimated Effort**: 30 minutes
- **File**: /static/js/tab1.js

## Status Tracking Enhancement
**Priority: Medium**
- **Task**: Implement proper contract status correlation in bedrock transformation
- **Issue**: items_on_contracts always shows 0 because contract correlation isn't implemented
- **Impact**: Users can't see which items are currently rented out
- **Estimated Effort**: 4-6 hours
- **Dependencies**: Contract correlation understanding

## Store Code Consistency
**Priority: Low**
- **Task**: Standardize store code mapping across all services
- **Issue**: Multiple store mapping approaches (pos_store_map vs store_mapping)
- **Impact**: Potential confusion, but works correctly
- **Estimated Effort**: 1-2 hours

## Enhanced Error Messages
**Priority: Low**
- **Task**: Add more descriptive error messages in bedrock services
- **Issue**: Generic "Bedrock service failed" messages
- **Impact**: Harder debugging for future issues
- **Estimated Effort**: 1 hour

## Performance Optimization
**Priority: Future**
- **Task**: Add caching layer to bedrock transformation service
- **Issue**: Every common names request hits database
- **Impact**: Could improve response times for repeated queries
- **Estimated Effort**: 3-4 hours
- **Dependencies**: Performance baseline measurement needed