import React from "react";
import { NavLink } from "react-router-dom";
import logo from "/Antar_IoT_Logo.png";

type Props = {
  children: React.ReactNode;
};

export const Layout: React.FC<Props> = ({ children }) => {
  return (
    <div className="app-root">
      <aside className="sidebar">
        <div className="sidebar-title">
          <img
            src={logo}
            alt="Antar IoT"
            style={{ maxWidth: "140px", height: "auto" }}
          />
        </div>
        <nav className="sidebar-nav">
          <NavLink
            to="/download"
            className={({ isActive }) =>
              isActive ? "nav-item active" : "nav-item"
            }
          >
            Download reports
          </NavLink>
          <NavLink
            to="/daily"
            className={({ isActive }) =>
              isActive ? "nav-item active" : "nav-item"
            }
          >
            Daily consumption
          </NavLink>
          <NavLink
            to="/presets"
            className={({ isActive }) =>
              isActive ? "nav-item active" : "nav-item"
            }
          >
            Device presets
          </NavLink>
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              isActive ? "nav-item active" : "nav-item"
            }
          >
            Settings
          </NavLink>
        </nav>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
};

