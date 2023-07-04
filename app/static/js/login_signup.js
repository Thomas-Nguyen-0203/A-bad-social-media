document.getElementById("submit").addEventListener("mousedown", async () =>{
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    let err = false;

    if (username.length == 0 || username.trim().length == 0)
    {
        document.getElementById("username_err").innerHTML = "<b>This field cannot be empty</b>";
        err = true;
    } 
    else if (/\s/.test(username.charAt(0)))
    {
        document.getElementById("username_err").innerHTML = "<b>This field cannot start with a whitespace</b>";
        err = true;
    } 
    else
        document.getElementById("username_err").innerHTML = "";

    if (password.length == 0)
    {
        document.getElementById("password_err").innerHTML = "<b>This field cannot be empty</b>";
        err = true;
    }
    else
    {
        document.getElementById("password_err").innerHTML = "";
    }

    if (err)
        return;

    let publicKey = null;
    
    if (document.getElementById("login") != null)
    {
        const subtle = window.crypto.subtle

        let keyPair = await subtle.generateKey(
        {
            name: "RSA-OAEP",
            modulusLength: 4096,
            publicExponent: new Uint8Array([0x01, 0x00, 0x01]),
            hash: "SHA-256"
        },
        true,
        ["encrypt", "decrypt"]
        );

        localStorage.setItem("private_key", JSON.stringify(await subtle.exportKey("jwk", keyPair.privateKey)));

        publicKey = JSON.stringify(await subtle.exportKey("jwk",keyPair.publicKey))
    }

    const post_url = document.location.href;
    let headers = new Headers();
    headers.append("Content-Type", "application/json");

    let response = await fetch(
        post_url,
        {
            method: "POST",
            headers: headers,
            body: JSON.stringify({
                username: username,
                password: password,
                public_key: publicKey
            })
        }
    );
    
    let new_url = await response.text();
    window.open(new_url, "_self");
});

document.getElementById("input").addEventListener("keydown", (event) =>{
    if (event.key == "Enter")
    {
        const event = new Event("mousedown");
        document.getElementById("submit").dispatchEvent(event);
    }
});