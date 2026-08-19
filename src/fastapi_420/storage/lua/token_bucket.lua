-- Token bucket rate limiting with Redis
-- KEYS[1] = rate limit key (hash)
-- ARGV[1] = limit
-- ARGV[2] = window seconds
-- ARGV[3] = cost
-- ARGV[4] = current timestamp
-- ARGV[5] = burst capacity (optional, defaults to limit)

local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local cost = tonumber(ARGV[3])
local now = tonumber(ARGV[4])
local capacity = tonumber(ARGV[5]) or limit

local rate = limit / window  -- tokens per second

local bucket = redis.call('HMGET', key, 'tokens', 'last_update')
local tokens = tonumber(bucket[1])
local last_update = tonumber(bucket[2])

if not tokens then
    tokens = capacity
    last_update = now
end

-- Refill tokens
local elapsed = now - last_update
tokens = math.min(capacity, tokens + elapsed * rate)

if tokens < cost then
    local needed = cost - tokens
    local retry_after = math.ceil(needed / rate)
    local reset_time = now + retry_after
    return {0, limit, 0, reset_time, retry_after}
end

tokens = tokens - cost
redis.call('HMSET', key, 'tokens', tokens, 'last_update', now)
redis.call('EXPIRE', key, math.ceil(capacity / rate) + window + 1)

local remaining = math.floor(tokens)
local reset_time = now + (capacity - tokens) / rate

return {1, limit, remaining, reset_time, 0}