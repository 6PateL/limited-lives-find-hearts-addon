package com.lifehearts;

import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import software.bernie.geckolib.model.GeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

@Mod.EventBusSubscriber(modid = LifeHearts.MOD_ID, value = Dist.CLIENT, bus = Mod.EventBusSubscriber.Bus.MOD)
public final class HeartClient {
    private HeartClient() {}

    public static class Model extends GeoModel<HeartEntity> {
        private static final ResourceLocation GEO = new ResourceLocation(LifeHearts.MOD_ID, "geo/heart.geo.json");
        private static final ResourceLocation TEX = new ResourceLocation(LifeHearts.MOD_ID, "textures/entity/heart.png");
        private static final ResourceLocation ANIM = new ResourceLocation(LifeHearts.MOD_ID, "animations/heart.animation.json");

        @Override
        public ResourceLocation getModelResource(HeartEntity e) {
            return GEO;
        }

        @Override
        public ResourceLocation getTextureResource(HeartEntity e) {
            return TEX;
        }

        @Override
        public ResourceLocation getAnimationResource(HeartEntity e) {
            return ANIM;
        }
    }

    public static class Renderer extends GeoEntityRenderer<HeartEntity> {
        public Renderer(EntityRendererProvider.Context ctx) {
            super(ctx, new Model());
            this.shadowRadius = 0.3F;
            addRenderLayer(new AutoGlowingGeoLayer<>(this)); // світні жили й іскри (heart_glowmask.png)
        }
    }

    @SubscribeEvent
    public static void onRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(LifeHearts.HEART.get(), Renderer::new);
    }
}
