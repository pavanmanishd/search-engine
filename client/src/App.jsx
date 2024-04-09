// import "./App.css";
import { useState } from "react";
// import axios from "axios";
function App() {
  const [search, setSearch] = useState("");
  const [Results, setResults] = useState([]);
  const handleSearch = () => {
    fetch("http://localhost:8000/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: search,
      }),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((data) => {
        // Handle the response data here
        // console.log(data);
        setResults(data);
      })
      .catch((error) => {
        // Handle errors here
        console.error("There was a problem with your fetch operation:", error);
      });
  };

  const ResultsList = Results.map((result, index) => (
    <div key={index}>
      {/* <h3>{result.title}</h3> */}
      <a href={result.url} target="_blank" rel="noreferrer">{result.title}</a>
    </div>
  ));

  return (
    <>
      <div>
        <p>Search</p>
        <input
          type="text"
          placeholder="Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button onClick={handleSearch}>Search</button>
      </div>
      <div>
        <p>Results</p>
        {ResultsList}
      </div>
    </>
  );
}

export default App;
