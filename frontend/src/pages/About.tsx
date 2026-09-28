export default function About() {
  return (
    <article className="prose">
      <h1>About Us</h1>
      <p className="lead">
        We’re a family-owned shop that has been selling official Yale merchandise in New Haven
        for about half a century, just steps from Yale’s campus.
      </p>

      <h2>Our Story</h2>
      <p>
        It started in 1975, when Barry Cobden set up a small Yale souvenir shop on Broadway.
        As the business grew, the family ended up running a few neighboring storefronts. In
        2007 they combined everything into a single larger space at 57 Broadway — a building
        that used to be a movie theater.
      </p>
      <p>
        The next generation, brothers Joel and Jeremy Cobden, now lead the company. Joel built
        up our printing side starting in the 1990s, while Jeremy looks after the store floor as
        well as production. A lot of our team has stuck with us for many years, and it’s not
        unusual for parents and their kids to have both worked behind our counter.
      </p>

      <h2>What We Do</h2>
      <ul>
        <li><strong>The store:</strong> Yale sweatshirts, tees and outerwear, plus smaller gifts and keepsakes for students, alumni and visitors.</li>
        <li><strong>Printing & embroidery:</strong> custom decoration done in our own workshop next door to the shop.</li>
        <li><strong>Design help:</strong> artwork, online team stores and order fulfillment for groups and organizations.</li>
        <li><strong>Branded goods:</strong> bags, cups, pens and other everyday items with your logo on them.</li>
      </ul>

      <h2>Locations</h2>
      <div className="info-grid">
        <div className="info-card">
          <h3>New Haven (Flagship Store)</h3>
          <p>57 Broadway<br />New Haven, CT 06511<br />203-789-1608</p>
        </div>
        <div className="info-card">
          <h3>Branford</h3>
          <p>184 Maple Street<br />Branford, CT 06405</p>
        </div>
        <div className="info-card">
          <h3>Florida</h3>
          <p>715 Bloom Street, Suite 140<br />Celebration, FL 34747</p>
        </div>
      </div>
      <p className="muted">Have a question? Reach us at team@campuscustoms.com.</p>
    </article>
  )
}
