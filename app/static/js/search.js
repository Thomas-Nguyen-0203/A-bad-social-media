const searchButton = document.getElementById("submit");

searchButton.addEventListener("mousedown", async () =>{
    const search_term = document.getElementById("username").value.trim();

    if (search_term.length == 0)
    {
        document.getElementById("error_msg").style.display = "block";
        return;
    }
    
    let new_url = (
        document.location.origin 
        + "/search/" 
        + search_term
    );

    window.open(new_url, "_self");
});

document.getElementById("username").addEventListener("keydown", (event)=>{
    if (event.key === "Enter")
    {
        const event = new Event("mousedown");

        searchButton.dispatchEvent(event);
    }
});