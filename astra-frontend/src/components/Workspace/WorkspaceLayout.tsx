import React from 'react';

interface WorkspaceLayoutProps {
  children: {
    left: React.ReactNode;
    right: React.ReactNode;
  };
}

export const WorkspaceLayout: React.FC<WorkspaceLayoutProps> = ({ children }) => {
  return (
    <div className="astra-workspace-split">
      <div className="astra-chat-pane">{children.left}</div>
      <div className="astra-canvas-pane">{children.right}</div>
    </div>
  );
};
