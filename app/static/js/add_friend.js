async function do_post_request(url)
{
    // Hardcoded url, should work for now.
    try
    {
        let request = await fetch(
            url,
            {
                method: "POST"
            }
        );
        const new_url = await request.text();
        window.open(new_url, "_self");
    } catch (e)
    {
        console.log(e.error);
        window.location.reload()
    }
    
}

let button = document.getElementById("AddFriendButton");

button.addEventListener("mousedown", ()=>{
    do_post_request(document.URL + "/add_friend");
});