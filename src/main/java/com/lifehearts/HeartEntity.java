package com.lifehearts;

import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.network.NetworkHooks;
import org.joml.Vector3f;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.UUID;

/**
 * Живе серце: висить у повітрі, б'ється, обертається. Кілька ударів гравця — і воно розлітається на шматки (анімація
 * break), а той, хто його розбив, отримує ще одне життя. ПКМ по серцю — поглинути його (анімація consume), теж життя.
 */
public class HeartEntity extends Entity implements GeoEntity {
    static final int ALIVE = 0, BREAKING = 1, CONSUMED = 2;
    private static final EntityDataAccessor<Integer> STATE = SynchedEntityData.defineId(HeartEntity.class, EntityDataSerializers.INT);
    private static final RawAnimation SPAWN = RawAnimation.begin().thenPlay("animation.heart.spawn").thenLoop("animation.heart.idle");
    private static final RawAnimation IDLE = RawAnimation.begin().thenLoop("animation.heart.idle");
    private static final RawAnimation BREAK = RawAnimation.begin().thenPlayAndHold("animation.heart.break");
    private static final RawAnimation CONSUME = RawAnimation.begin().thenPlayAndHold("animation.heart.consume");

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private int hits;
    private int stateTicks;
    private int age;
    private UUID winner;

    public HeartEntity(EntityType<? extends HeartEntity> type, Level level) {
        super(type, level);
        this.noPhysics = true;
        this.setNoGravity(true);
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(STATE, ALIVE);
    }

    int state() {
        return this.entityData.get(STATE);
    }

    @Override
    public void tick() {
        super.tick();
        this.setDeltaMovement(Vec3.ZERO);
        if (!(level() instanceof ServerLevel level)) {
            return;
        }
        age++;
        int s = state();
        if (s == ALIVE) {
            if (age % 10 == 0) {
                level.sendParticles(new DustParticleOptions(new Vector3f(0.9F, 0.1F, 0.15F), 1.0F), getX(), getY() + 0.6D, getZ(), 2,
                        0.35D, 0.35D, 0.35D, 0.0D);
            }
            if (age % 20 == 0) {
                level.playSound(null, blockPosition(), SoundEvents.WARDEN_HEARTBEAT, SoundSource.NEUTRAL, 0.5F, 1.4F);
            }
            int life = HeartConfig.LIFETIME_MINUTES.get();
            if (life > 0 && age > life * 1200) {
                level.sendParticles(ParticleTypes.POOF, getX(), getY() + 0.5D, getZ(), 15, 0.3D, 0.3D, 0.3D, 0.02D);
                LifeHearts.LOG.info("[LifeHearts] heart at {} faded (nobody broke it)", blockPosition().toShortString());
                discard();
            }
            return;
        }
        stateTicks++;
        if (s == BREAKING && stateTicks == 4) {
            level.playSound(null, blockPosition(), SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.NEUTRAL, 1.2F, 0.6F);
            level.playSound(null, blockPosition(), SoundEvents.SLIME_BLOCK_BREAK, SoundSource.NEUTRAL, 1.0F, 0.6F);
            level.sendParticles(new DustParticleOptions(new Vector3f(0.95F, 0.08F, 0.1F), 1.6F), getX(), getY() + 0.6D, getZ(), 40,
                    0.5D, 0.5D, 0.5D, 0.0D);
        }
        // після анімації: життя летить до гравця і зараховується
        int length = s == BREAKING ? 20 : 24;
        if (stateTicks == length) {
            grant(level);
            discard();
        }
    }

    // ------------------------------------------------------------------ удари і поглинання

    @Override
    public boolean isPickable() {
        return state() == ALIVE;
    }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        if (level().isClientSide || state() != ALIVE || !(source.getEntity() instanceof ServerPlayer p)) {
            return false;
        }
        hits++;
        ServerLevel level = (ServerLevel) level();
        level.playSound(null, blockPosition(), SoundEvents.AMETHYST_BLOCK_HIT, SoundSource.NEUTRAL, 1.0F, 0.7F + hits * 0.1F);
        level.sendParticles(ParticleTypes.DAMAGE_INDICATOR, getX(), getY() + 0.6D, getZ(), 4, 0.3D, 0.3D, 0.3D, 0.1D);
        if (hits >= HeartConfig.HITS.get()) {
            winner = p.getUUID();
            this.entityData.set(STATE, BREAKING);
            stateTicks = 0;
        }
        return true;
    }

    @Override
    public InteractionResult interact(Player player, InteractionHand hand) {
        if (state() != ALIVE) {
            return InteractionResult.PASS;
        }
        if (!level().isClientSide) {
            winner = player.getUUID();
            this.entityData.set(STATE, CONSUMED);
            stateTicks = 0;
            level().playSound(null, blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 1.0F, 1.2F);
        }
        return InteractionResult.sidedSuccess(level().isClientSide);
    }

    private void grant(ServerLevel level) {
        ServerPlayer p = winner == null ? null : level.getServer().getPlayerList().getPlayer(winner);
        if (p == null) {
            return;
        }
        // слід із частинок від серця до гравця
        Vec3 from = position().add(0.0D, 0.6D, 0.0D), to = p.position().add(0.0D, 1.0D, 0.0D);
        for (int i = 0; i <= 16; i++) {
            Vec3 at = from.add(to.subtract(from).scale(i / 16.0D));
            level.sendParticles(new DustParticleOptions(new Vector3f(1.0F, 0.25F, 0.3F), 1.2F), at.x, at.y, at.z, 2, 0.05D, 0.05D, 0.05D, 0.0D);
        }
        int lives = Lives.giveLife(p);
        if (lives == -2) {
            // життя вже повні: серце лікує
            p.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 200, 1));
            p.addEffect(new MobEffectInstance(MobEffects.ABSORPTION, 1200, 1));
            p.displayClientMessage(Component.translatable("msg.lifehearts.full").withStyle(ChatFormatting.GOLD), true);
            p.playNotifySound(SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 1.0F, 1.2F);
            LifeHearts.LOG.info("[LifeHearts] {} took a heart, lives already full: healed instead", p.getName().getString());
            return;
        }
        if (lives == -1) {
            p.addEffect(new MobEffectInstance(MobEffects.ABSORPTION, 2400, 3));
            p.displayClientMessage(Component.translatable("msg.lifehearts.nomod").withStyle(ChatFormatting.GOLD), true);
            LifeHearts.LOG.info("[LifeHearts] {} took a heart, Limited Lives not available: absorption instead", p.getName().getString());
            return;
        }
        Net.sendLifeFx(p, lives);
        // посвячення: урочисті звуки лише для нього
        p.playNotifySound(SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 1.0F, 1.0F);
        p.playNotifySound(SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 1.0F, 1.3F);
        p.playNotifySound(SoundEvents.TOTEM_USE, SoundSource.PLAYERS, 0.4F, 1.4F);
        level.sendParticles(ParticleTypes.TOTEM_OF_UNDYING, p.getX(), p.getY() + 1.0D, p.getZ(), 60, 0.5D, 1.0D, 0.5D, 0.3D);
        p.sendSystemMessage(Component.translatable("msg.lifehearts.gained", lives).withStyle(ChatFormatting.RED, ChatFormatting.BOLD));
        LifeHearts.LOG.info("[LifeHearts] {} gained a life from a heart at {}: now {} lives", p.getName().getString(), blockPosition().toShortString(), lives);
    }

    // ------------------------------------------------------------------ інше

    @Override
    public boolean isAttackable() {
        return true;
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    public boolean shouldRenderAtSqrDistance(double d) {
        return d < 96.0D * 96.0D;
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        hits = tag.getInt("Hits");
        age = tag.getInt("Age");
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
        tag.putInt("Hits", hits);
        tag.putInt("Age", age);
    }

    @Override
    public Packet<ClientGamePacketListener> getAddEntityPacket() {
        return NetworkHooks.getEntitySpawningPacket(this);
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "main", 2, st -> {
            int s = state();
            if (s == BREAKING) {
                return st.setAndContinue(BREAK);
            }
            if (s == CONSUMED) {
                return st.setAndContinue(CONSUME);
            }
            return st.setAndContinue(tickCount < 16 ? SPAWN : IDLE);
        }));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
