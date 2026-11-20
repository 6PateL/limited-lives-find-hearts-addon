package com.lifehearts;

import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.network.NetworkEvent;
import net.minecraftforge.network.NetworkRegistry;
import net.minecraftforge.network.PacketDistributor;
import net.minecraftforge.network.simple.SimpleChannel;

import java.util.function.Supplier;

public final class Net {
    public static final SimpleChannel CHANNEL = NetworkRegistry.newSimpleChannel(new ResourceLocation(LifeHearts.MOD_ID, "main"),
            () -> "1", v -> true, v -> true);

    private Net() {}

    static void register() {
        CHANNEL.registerMessage(0, LifeFx.class, LifeFx::encode, LifeFx::decode, LifeFx::handle);
    }

    static void sendLifeFx(ServerPlayer p, int lives) {
        CHANNEL.send(PacketDistributor.PLAYER.with(() -> p), new LifeFx(lives));
    }

    public record LifeFx(int lives) {
        static void encode(LifeFx m, FriendlyByteBuf buf) {
            buf.writeVarInt(m.lives);
        }

        static LifeFx decode(FriendlyByteBuf buf) {
            return new LifeFx(buf.readVarInt());
        }

        static void handle(LifeFx m, Supplier<NetworkEvent.Context> ctx) {
            ctx.get().enqueueWork(() -> DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> () -> LifeOverlay.start(m.lives)));
            ctx.get().setPacketHandled(true);
        }
    }
}
