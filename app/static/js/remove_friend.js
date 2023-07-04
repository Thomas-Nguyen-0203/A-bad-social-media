async function do_post_request(url)
{
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

let button = document.getElementById("RemoveFriendButton");

button.addEventListener("mousedown", ()=>{
    do_post_request(document.URL + "/remove_friend");
});