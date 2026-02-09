import React from 'react';
// Navigate up one level from 'pages' to 'src', then into 'styles'
import '../styles/MaintenancePopup.css';

const MaintenanceOverlay = () => {
  return (
    <div className="maintenance-overlay">
      <div className="maintenance-popup">
        <h2>We’re currently performing maintenance!</h2>
        <p>Thank you for your patience</p>
      </div>
    </div>
  );
};

export default MaintenanceOverlay;