package com.lifehearts;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** Серця самі з'являються біля гравців: зрідка, на поверхні або в печерах, у вільному повітрі над твердим блоком. */
@Mod.EventBusSubscriber(modid = LifeHearts.MOD_ID)
public final class HeartSpawner {
    private HeartSpawner() {}

    @SubscribeEvent
    public static void onTick(TickEvent.ServerTickEvent event) {
        if (event.phase != TickEvent.Phase.END || !HeartConfig.ENABLED.get()) {
            return;
        }
        int every = HeartConfig.CHECK_SECONDS.get() * 20;
        if (event.getServer().getTickCount() % every != 0) {
            return;
        }
        for (ServerPlayer p : event.getServer().getPlayerList().getPlayers()) {
            if (p.isSpectator() || p.getRandom().nextDouble() >= HeartConfig.CHANCE.get()) {
                continue;
            }
            ServerLevel level = p.serverLevel();
            int near = level.getEntitiesOfClass(HeartEntity.class, new AABB(p.blockPosition()).inflate(160.0D, 128.0D, 160.0D)).size();
            if (near >= HeartConfig.MAX_NEARBY.get()) {
                continue;
            }
            BlockPos at = spot(level, p.blockPosition(), HeartConfig.MIN_DIST.get(), HeartConfig.MAX_DIST.get());
            if (at != null) {
                spawn(level, at);
                LifeHearts.LOG.info("[LifeHearts] a heart appeared at {} near {} ({})", at.toShortString(), p.getName().getString(),
                        level.dimension().location());
            }
        }
    }

    static void spawn(ServerLevel level, BlockPos at) {
        HeartEntity h = LifeHearts.HEART.get().create(level);
        if (h == null) {
            return;
        }
        h.moveTo(at.getX() + 0.5D, at.getY() + 0.6D, at.getZ() + 0.5D, level.random.nextFloat() * 360.0F, 0.0F);
        level.addFreshEntity(h);
    }

    /** Вільне місце (2 блоки повітря над твердим блоком, без рідини) на відстані min..max, у чанку, що оновлюється. */
    static BlockPos spot(ServerLevel level, BlockPos around, int min, int max) {
        for (int i = 0; i < 24; i++) {
            double a = level.random.nextDouble() * Math.PI * 2.0D;
            double d = min + level.random.nextDouble() * Math.max(1, max - min);
            int x = (int) Math.floor(around.getX() + Math.cos(a) * d);
            int z = (int) Math.floor(around.getZ() + Math.sin(a) * d);
            BlockPos col = new BlockPos(x, around.getY(), z);
            if (!level.hasChunkAt(col) || !level.isPositionEntityTicking(col)) {
                continue;
            }
            // шукаємо порожнину неподалік від висоти гравця: у печерах серце з'явиться в печері, нагорі — нагорі
            int y0 = around.getY() + level.random.nextInt(17) - 8;
            for (int dy = 0; dy < 24; dy++) {
                for (int sgn = -1; sgn <= 1; sgn += 2) {
                    int y = y0 + dy * sgn;
                    if (y <= level.getMinBuildHeight() + 1 || y >= level.getMaxBuildHeight() - 2) {
                        continue;
                    }
                    BlockPos p = new BlockPos(x, y, z);
                    BlockState floor = level.getBlockState(p.below());
                    if (level.getBlockState(p).isAir() && level.getBlockState(p.above()).isAir()
                            && floor.isSolidRender(level, p.below()) && level.getFluidState(p).isEmpty()) {
                        return p;
                    }
                }
            }
        }
        return null;
    }
}
