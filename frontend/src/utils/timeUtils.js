/**
 * Railway ETA System - Time and Delay Formatting Utilities
 * Converts raw minute offsets and delay durations into passenger-friendly clock times and delay badges.
 */

/**
 * Convert a base departure time string ("HH:MM") and minute offset into formatted clock time.
 * Supports 12-hour AM/PM and 24-hour formats with day-rollover support.
 * 
 * @param {string} originTimeStr Base departure time, e.g. "06:00" or "16:30"
 * @param {number} offsetMinutes Minutes from origin departure
 * @param {number} delayMinutes Optional delay in minutes to add
 * @param {boolean} use12Hour Whether to return 12-hour format with AM/PM (default: true)
 * @returns {string} Formatted clock time, e.g. "08:30 AM" or "10:15 PM (+1d)"
 */
export function formatClockTime(originTimeStr = '10:00', offsetMinutes = 0, delayMinutes = 0, use12Hour = true) {
  if (!originTimeStr) originTimeStr = '10:00'
  const parts = String(originTimeStr).split(':')
  const baseHour = parseInt(parts[0] || '10', 10)
  const baseMin = parseInt(parts[1] || '00', 10)

  const totalMin = baseHour * 60 + baseMin + Math.round(Number(offsetMinutes) || 0) + Math.round(Number(delayMinutes) || 0)

  // Day rollover
  const dayOffset = Math.floor(totalMin / (24 * 60))
  const dayMinutes = ((totalMin % (24 * 60)) + (24 * 60)) % (24 * 60)
  const hour = Math.floor(dayMinutes / 60)
  const minute = Math.floor(dayMinutes % 60)

  const padMin = String(minute).padStart(2, '0')

  if (use12Hour) {
    const period = hour >= 12 ? 'PM' : 'AM'
    const h12 = hour % 12 === 0 ? 12 : hour % 12
    const timeStr = `${h12}:${padMin} ${period}`
    return dayOffset > 0 ? `${timeStr} (+${dayOffset}d)` : timeStr
  } else {
    const padHour = String(hour).padStart(2, '0')
    const timeStr = `${padHour}:${padMin}`
    return dayOffset > 0 ? `${timeStr} (+${dayOffset}d)` : timeStr
  }
}

/**
 * Format a delay value in minutes into intuitive passenger-friendly text.
 * E.g.
 *   0 => "On Time"
 *   12 => "+12 min"
 *   77.8 => "+1 hr 18 min"
 *   150 => "+2 hr 30 min"
 */
export function formatDelayHuman(delayMinutes) {
  const d = Math.round(Number(delayMinutes) || 0)
  if (d <= 0) return 'On Time'
  if (d < 60) return `+${d} min`
  const hours = Math.floor(d / 60)
  const mins = d % 60
  if (mins === 0) return `+${hours} hr`
  return `+${hours} hr ${mins} min`
}

/**
 * Format short delay for compact badges, e.g. "+1h 18m" or "On Time"
 */
export function formatDelayShort(delayMinutes) {
  const d = Math.round(Number(delayMinutes) || 0)
  if (d <= 0) return 'On Time'
  if (d < 60) return `+${d}m`
  const hours = Math.floor(d / 60)
  const mins = d % 60
  return mins === 0 ? `+${hours}h` : `+${hours}h ${mins}m`
}

/**
 * Format halt duration in minutes
 * e.g. 0 => "Passing (0m)", 2 => "2 min halt", 60 => "1 hr halt"
 */
export function formatHalt(haltMin) {
  const h = Number(haltMin) || 0
  if (h <= 0) return 'Pass'
  if (h < 60) return `${h}m halt`
  const hrs = Math.floor(h / 60)
  const mins = h % 60
  return mins > 0 ? `${hrs}h ${mins}m` : `${hrs}h halt`
}
