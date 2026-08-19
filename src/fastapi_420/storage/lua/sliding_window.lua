-- Sliding window rate limiting with Redis
-- KEYS[1] = rate limit key (sorted set)
-- ARGV[1] = limit
-- ARGV[2] = window seconds
-- ARGV[3] = cost
-- ARGV[4] = current timestamp
-- ARGV[5] = request ID (unique)

local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local cost = tonumber(ARGV[3])
local now = tonumber(ARGV[4])
local request_id = ARGV[5]

local cutoff = now - window

-- Remove old entries
redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)

-- Count current requests
local current = redis.call('ZCARD', key)

if current + cost > limit then
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local reset_time = 0
    if #oldest > 0 then
        reset_time = tonumber(oldest[2]) + window
    else
        reset_time = now + window
    end
    local retry_after = math.ceil(reset_time - now)
    return {0, limit, 0, reset_time, retry_after}
end

-- Add new requests
for i = 1, cost do
    redis.call('ZADD', key, now, request_id .. ":" .. i)
end

redis.call('EXPIRE', key, window + 1)

local remaining = limit - current - cost
local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
local reset_time = 0
if #oldest > 0 then
    reset_time = tonumber(oldest[2]) + window
else
    reset_time = now + window
end

return {1, limit, remaining, reset_time, 0}