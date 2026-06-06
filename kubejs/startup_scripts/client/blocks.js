const client_basic_blocks = [

]

StartupEvents.registry("block", event => {

    for (let blockId of client_basic_blocks) {
        event.create(`elysium:${blockId}`)
    }
  
    event.create("elysium:emerald_chest")
        .property(BlockProperties.HORIZONTAL_FACING)
        .placementState(ctx => {
            ctx.setValue(
                BlockProperties.HORIZONTAL_FACING,
                ctx.getHorizontalDirection().getOpposite()
            )
        })
})