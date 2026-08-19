-- Fixed window rate limiting with Redis
-- KEYS[1] = rate limit key
-- ARGV[1] = limit
-- ARGV[2] = window seconds
-- ARGV[3] = cost
-- ARGV[4] = current timestamp

local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local cost = tonumber(ARGV[3])
local now = tonumber(ARGV[4])

local window_start = now - (now % window)
local window_key = key .. ":" .. window_start

local current = redis.call('GET', window_key)
current = current and tonumber(current) or 0

if current + cost > limit then
    local ttl = window - (now - window_start) + 1
    return {0, limit, 0, window_start + window, ttl}
end

local new_count = redis.call('INCRBY', window_key, cost)
if new_count == cost then
    redis.call('EXPIRE', window_key, window + 1)
end

local remaining = limit - new_count
return {1, limit, remaining, window_start + window, 0}