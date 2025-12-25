
fetch("http://localhost:8000/match?figma_url=x&website_url=y", {
  method: "POST"
})
.then(res => res.json())
.then(data => {
  document.getElementById("output").innerText =
    JSON.stringify(data, null, 2);
});
