import { useEffect, useState } from 'react';
import { Outlet, NavLink } from "react-router-dom";
import * as fcl from "@onflow/fcl";
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';
import './App.css';

import "./flow/config";
import { Navbar, Nav, Container, Dropdown } from 'react-bootstrap';

export default function Layout() {
  const [user, setUser] = useState({ loggedIn: null });

  useEffect(() => {
    fcl.currentUser().subscribe(setUser);
  }, []);

  const handleConnect = () => {
    fcl.authenticate();
  };

  const handleDisconnect = () => {
    fcl.unauthenticate();
  };

  return (
    <>
      {/* Navbar */}
      <Navbar expand="lg" className="navbar mb-3">
        <Container fluid>
          <Navbar.Brand as={NavLink} to="/">
            <img
              src="/favicon.png"
              alt="MVP on Flow Logo"
              height="40"
              className="me-2"
            />
          </Navbar.Brand>

          {/* Burger toggle with gold color */}
          <Navbar.Toggle
            aria-controls="navbarNav"
            style={{
              borderColor: '#FDB927',
              color: '#FDB927'
            }}
          >
            <span
              className="navbar-toggler-icon"
              style={{ filter: 'invert(80%) sepia(100%) saturate(400%) hue-rotate(10deg)' }}
            />
          </Navbar.Toggle>

          <Navbar.Collapse id="navbarNav">
            <Nav className="me-auto mb-2 mb-lg-0">
              <Nav.Link as={NavLink} to="/">Home</Nav.Link>
              <Nav.Link as={NavLink} to="/swapfest">Swapfest</Nav.Link>
              <Nav.Link as={NavLink} to="/vote">Vote</Nav.Link>

                {/* Buy $MVP button */}
                <Nav.Link
                  id="buy-mvp"
                  href="https://app.increment.fi/swap?in=A.1654653399040a61.FlowToken&out=A.6fd2465f3a22e34c.PetJokicsHorses"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-sm ms-lg-2 mt-2 mt-lg-0"
                  style={{ fontWeight: 600, borderRadius: '8px' }}
                  onClick={(e) => e.currentTarget.blur()}   // drop focus so it doesn’t look “stuck”
                >
                  💰 Buy $MVP
                </Nav.Link>

            </Nav>

            <div className="d-flex align-items-center">
              {user.loggedIn ? (
                <>
                  <span className="wallet-address me-2">{user.addr}</span>
                  <button
                    className="btn-wallet"
                    onClick={handleDisconnect}
                  >
                    Disconnect
                  </button>
                </>
              ) : (
                <button
                  className="btn-wallet"
                  onClick={handleConnect}
                >
                  Connect Wallet
                </button>
              )}
            </div>
          </Navbar.Collapse>
        </Container>
      </Navbar>

      {/* Main Content */}
      <div className="container-fluid mt-4 flex-grow-1">
        <Outlet />
      </div>

      {/* Footer */}
      <div className="footer mt-auto">
        <p>
          This is a fan project and is not affiliated with NBA TopShot, Nikola Jokić, or any official organization.
        </p>
        <div className="d-flex justify-content-center align-items-center gap-3 mt-2">
          <a href="https://discord.gg/3p3ff9PHqW" target="_blank" aria-label="Discord" rel="noreferrer">
            <i className="bi bi-discord" style={{ fontSize: '1.5rem' }}></i>
          </a>
          <a href="https://x.com/petjokicshorses" target="_blank" aria-label="Twitter" rel="noreferrer">
            <i className="bi bi-twitter-x" style={{ fontSize: '1.5rem' }}></i>
          </a>
        </div>
      </div>
    </>
  );
}
