export function formatDate(isoDateString) {
  if (!isoDateString || isoDateString === 'N/A') return 'N/A';
  try {
    const date = new Date(isoDateString);
    if (isNaN(date.getTime())) return 'N/A';

    const days = ['Sun', 'Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat'];
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    const dayName = days[date.getDay()];
    const monthName = months[date.getMonth()];
    const day = date.getDate();
    const year = date.getFullYear();
    let hour = date.getHours();
    const minute = date.getMinutes().toString().padStart(2, '0');
    const ampm = hour >= 12 ? 'pm' : 'am';
    hour = hour % 12 || 12;

    return `${dayName}, ${monthName} ${day} ${year} ${hour}:${minute} ${ampm}`;
  } catch (error) {
    console.error('formatDate error:', error.message);
    return 'N/A';
  }
}
