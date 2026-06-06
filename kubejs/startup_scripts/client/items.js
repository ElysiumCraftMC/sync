const client_basic_items = [
    "emerald_key",
    "rusty_key",
    "rusty_key_fragment"
]

StartupEvents.registry("item", event => {

    for (let itemId of client_basic_items) {
        event.create(`elysium:${itemId}`)
    }
    
})