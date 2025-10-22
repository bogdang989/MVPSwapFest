import React from 'react';

export default function Home() {
  return (
    <>
      <div className="hero">
        <h1>🏀 MVP on Flow - Pet Jokic's Horses 🐎</h1>
        <p>
          MVP on Flow, also known as <strong>Pet Jokic's horses</strong>, is a <strong>fan-powered project</strong> celebrating Nikola Jokic and his NBA TopShot moments on the Flow blockchain.
        </p>
        <p>
          Join our Discord community for Jokic-themed fun, prediction contests, raffles, giveaways, and more!
        </p>
        <p>
          Earn and use <strong>$MVP</strong> tokens in community games, swap them for Jokic moments, trade them on Flow exchanges or stake them to earn rewards. Whether you're a collector or a fan, there's something for everyone.
        </p>
        <a
          href="https://discord.gg/3p3ff9PHqW"
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-discord"
        >
          <i className="bi bi-discord"></i> Join Our Discord
        </a>
      </div>

      <div className="card shadow mb-4">
        <div className="card-body">
          <h2 className="card-title text-center mb-3">💰 $MVP Tokenomics, Exchange and Rewards</h2>
          <p className="card-text text-center">
            Learn how $MVP works: buy, sell or swap Jokic moments using $MVP
          </p>
          <div className="text-center mt-3">
            <img
              src="/images/Tokenomics.svg"
              alt="MVP Tokenomics"
              className="img-fluid rounded shadow"
            />
          </div>
        </div>
      </div>
    </>
  );
}
