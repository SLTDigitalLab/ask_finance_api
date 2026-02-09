export const getMaintenanceStatus = () => {
  const envValue = import.meta.env.VITE_MAINTENANCE_MODE;

  // 1. Check .env variable
  if (envValue !== undefined && envValue !== '') {
    return envValue === 'true';
  }

  // 2. Hardcoded Fallback (Change this manually if not using .env)
  // true for Maintananc Mode On 
  return false; 
};