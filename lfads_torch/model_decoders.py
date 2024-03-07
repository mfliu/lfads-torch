from typing import Any, Dict, Literal, Tuple, Union, List

import pytorch_lightning as pl
import torch
from torch import nn

from .metrics import ExpSmoothedMetric, r2_score, regional_bits_per_spike
from .modules import augmentations
from .modules.decoder import Decoder
from .modules.encoder import Encoder
from .modules.l2 import compute_l2_penalty
from .modules.priors import Null
from .tuples import SessionBatch, SessionOutput
from .utils import transpose_lists

import copy

class LFADS(pl.LightningModule):
    def __init__(
        self,
        encod_data_dim: int,
        encod_seq_len: int,
        recon_region_name: List[str],
        recon_data_dim: List[int],
        recon_seq_len: List[int],
        ext_input_dim: int,
        ic_enc_seq_len: int,
        ic_enc_dim: int,
        ci_enc_dim: List[int],
        ci_lag: List[int],
        con_dim: List[int],
        co_dim: List[int],
        ic_dim: int,
        gen_dim: List[int],
        fac_dim: List[int],
        dropout_rate: float,
        reconstruction: nn.ModuleList,
        variational: bool,
        co_prior: List[nn.Module],
        ic_prior: List[nn.Module],
        ic_post_var_min: float,
        cell_clip: float,
        train_aug_stack: augmentations.AugmentationStack,
        infer_aug_stack: augmentations.AugmentationStack,
        readin: nn.ModuleList,
        region_readin: List[nn.ModuleList],
        region_std: List[nn.ModuleList],
        readout: nn.ModuleList,
        loss_scale: float,
        recon_reduce_mean: bool,
        lr_scheduler: bool,
        lr_init: float,
        lr_stop: float,
        lr_decay: float,
        lr_patience: int,
        lr_adam_beta1: float,
        lr_adam_beta2: float,
        lr_adam_epsilon: float,
        weight_decay: float,
        l2_start_epoch: int,
        l2_increase_epoch: int,
        l2_ic_enc_scale: float,
        l2_ci_enc_scale: List[float],
        l2_gen_scale: List[float],
        l2_con_scale: List[float],
        kl_start_epoch: int,
        kl_increase_epoch: int,
        kl_ic_scale: List[float],
        kl_co_scale: List[float],
        
<<<<<<< HEAD
        kl_co_scale_BS: float,
        kl_ic_scale_BS: float,
        l2_gen_scale_BS: float,
        l2_con_scale_BS: float,

=======
>>>>>>> c3e6c47abde239856b5e0d56f96e2278c12e7c25
        kl_co_scale_CTX: float,
        kl_ic_scale_CTX: float,
        l2_gen_scale_CTX: float,
        l2_con_scale_CTX: float, 

        kl_co_scale_FRP: float,
        kl_ic_scale_FRP: float,
        l2_gen_scale_FRP: float,
        l2_con_scale_FRP: float,
<<<<<<< HEAD
        
        kl_co_scale_HPF: float,
        kl_ic_scale_HPF: float,
        l2_gen_scale_HPF: float,
        l2_con_scale_HPF: float,
        
        kl_co_scale_MB: float,
        kl_ic_scale_MB: float,
        l2_gen_scale_MB: float,
        l2_con_scale_MB: float,
=======

        kl_co_scale_STR: float,
        kl_ic_scale_STR: float,
        l2_gen_scale_STR: float,
        l2_con_scale_STR: float,
>>>>>>> c3e6c47abde239856b5e0d56f96e2278c12e7c25

        kl_co_scale_TH: float,
        kl_ic_scale_TH: float,
        l2_gen_scale_TH: float,
        l2_con_scale_TH: float
    ):
        """
        Initialize the LFADS model.

        Parameters
        ----------
        encod_data_dim : int
            Dimensionality of the encoding data.
        encod_seq_len : int
            Sequence length of the encoding data.
        recon_seq_len : int
            Sequence length of the reconstruction data.
        ext_input_dim : int
            Dimensionality of the external input.
        ic_enc_seq_len : int
            Time steps to be used for only the initial condition encoder.
        ic_enc_dim : int
            Dimensionality of the initial condition encoder.
        ci_enc_dim : int
            Dimensionality of the controller input encoder.
        ci_lag : int
            Lag of the controller input.
        con_dim : int
            Dimensionality of the controller.
        co_dim : int
            Dimensionality of the controller output.
        ic_dim : int
            Dimensionality of the initial condition.
        gen_dim : int
            Dimensionality of the generator.
        fac_dim : int
            Dimensionality of the factors.
        dropout_rate : float
            Dropout rate.
        reconstruction : nn.ModuleList
            List of reconstruction modules.
        variational : bool
            Whether to use variational inference.
        co_prior : nn.Module
            Prior distribution for the controller output.
        ic_prior : nn.Module
            Prior distribution for the initial condition.
        ic_post_var_min : float
            Minimum variance for the initial condition posterior.
        cell_clip : float
            Value to clip the cell states at.
        train_aug_stack : augmentations.AugmentationStack
            Stack of data augmentations to apply during training.
        infer_aug_stack : augmentations.AugmentationStack
            Stack of data augmentations to apply during inference.
        readin : nn.ModuleList
            List of read-in modules.
        readout : nn.ModuleList
            List of read-out modules.
        loss_scale : float
            Scaling factor for the loss.
        recon_reduce_mean : bool
            Whether to reduce the reconstruction loss by taking the mean.
        lr_scheduler : bool
            Whether to use a learning rate scheduler.
        lr_init : float
            Initial learning rate.
        lr_stop : float
            Stopping threshold for learning rate.
        lr_decay : float
            Learning rate decay factor.
        lr_patience : int
            Number of epochs to wait before reducing the learning rate.
        lr_adam_beta1 : float
            Beta1 parameter for the Adam optimizer.
        lr_adam_beta2 : float
            Beta2 parameter for the Adam optimizer.
        lr_adam_epsilon : float
            Epsilon parameter for the Adam optimizer.
        weight_decay : float
            Weight decay factor.
        l2_start_epoch : int
            Epoch to start applying L2 regularization.
        l2_increase_epoch : int
            Number of epochs over which to increase the L2 regularization.
        l2_ic_enc_scale : float
            Scaling factor for the L2 regularization of the initial condition encoder.
        l2_ci_enc_scale : float
            Scaling factor for the L2 regularization of the controller input encoder.
        l2_gen_scale : float
            Scaling factor for the L2 regularization of the generator.
        l2_con_scale : float
            Scaling factor for the L2 regularization of the controller.
        kl_start_epoch : int
            Epoch to start applying KL divergence regularization.
        kl_increase_epoch : int
            Number of epochs over which to increase the KL divergence regularization.
        kl_ic_scale : float
            Scaling factor for the KL divergence regularization of the initial condition.
        kl_co_scale : float
            Scaling factor for the KL divergence regularization of the controller output.
        """
        super().__init__()
        self.save_hyperparameters(
            ignore=["ic_prior", "co_prior", "reconstruction", "readin", "readout"],
            logger=False
        )
        
        decoder_hps = ["recon_seq_len", "ci_enc_dim", "ci_lag", "con_dim", "co_dim", "gen_dim", "fac_dim",\
                       "co_prior", "l2_ci_enc_scale", "l2_gen_scale", "kl_co_scale"]
        
        # Store `co_prior` on `hparams` so it can be accessed in decoder
        self.hparams.co_prior = co_prior
        # Make sure the nn.ModuleList arguments are all the same length
        ## MFL: These are nn.ModuleList and not one for each decoder because decoder outputs will be merged across regions and have the same reconstruction
        assert len(readin) == len(readout) == len(reconstruction)
        # Make sure that non-variational models use null priors
        if not variational:
            assert isinstance(ic_prior, Null) and isinstance(co_prior, Null)
        # Store the readin network
        self.readin = readin
        self.region_readin = region_readin
        self.region_std = region_std
        # Decide whether to use the controller
        self.use_con = [all([ci_enc_dim[x] > 0, con_dim[x] > 0, co_dim[x] > 0]) for x in range(0, len(ci_enc_dim))]
        # Create the encoder and decoder
        self.encoder = Encoder(hparams=self.hparams)
        self.decoders = []
        for d in range(0, len(recon_seq_len)):
            decoder_hparams = copy.deepcopy(self.hparams)
            for dhp in decoder_hps:
                decoder_hparams[dhp] = self.hparams[dhp][d]
            self.decoders.append(Decoder(hparams=decoder_hparams))
        # Store the readout network
        self.readout = readout
        # Create object to manage reconstruction
        self.recon = reconstruction
        # Store the trainable priors
        self.ic_prior = ic_prior
        self.co_prior = co_prior
        # Create metric for exponentially-smoothed `valid/recon`
        self.valid_recon_smth = ExpSmoothedMetric(coef=0.3)
        # Store the data augmentation stacks
        self.train_aug_stack = train_aug_stack
        self.infer_aug_stack = infer_aug_stack

    def forward(
        self,
        batch: Dict[int, SessionBatch],
        sample_posteriors: bool = False,
        output_means: bool = True,
    ) -> Dict[int, SessionOutput]:
        """
        Forward pass through the model.

        Parameters
        ----------
        batch : Dict[int, SessionBatch]
            A dictionary of SessionBatch objects, where each key is a session index and each value is a SessionBatch object.
        sample_posteriors : bool, optional
            If True, samples from the posterior distributions, otherwise passes the mean. Default is False.
        output_means : bool, optional
            If True, converts the output parameters to means. Otherwise outputs distribution parameters. Default is True.

        Returns
        -------
        Dict[int, SessionOutput]
            A dictionary of SessionOutput objects, where each key is a session and each value is a SessionOutput object.
        """
        #import pdb; pdb.set_trace()
        
        # Allow SessionBatch input
        if type(batch) == SessionBatch and len(self.readin) == 1:
            batch = {0: batch}
        # Determine which sessions are in the batch
        sessions = sorted(batch.keys())
        # Keep track of batch sizes so we can split back up
        batch_sizes = [len(batch[s].encod_data) for s in sessions]
        # Pass the data through the readin networks
        encod_data = torch.cat([self.readin[s](batch[s].encod_data) for s in sessions])
        # Collect the external inputs
        ext_input = torch.cat([batch[s].ext_input for s in sessions])
        # Pass the data through the encoders
        ## MFL: All controllers have the same initial condition, but each decoder (region) gets its own controller
        ic_mean, ic_std, ci = self.encoder(encod_data)
        
        # Create the posterior distribution over initial conditions
        #ic_post = self.ic_prior.make_posterior(ic_mean, ic_std)
        # Choose to take a sample or to pass the mean
        # ic_samp = ic_post.rsample() if sample_posteriors else ic_mean
        ## MFL: In this instance, ic_samp shouldn't be used, because g0 for each area should just be some linear transformation 
        ## on the pre-trial activity of each region. ALM encoder and controller only determines the controller input for each region
        ## MFL: region_readout is a List of ModuleLists--each ModuleList is a list of linear layers for a region in each session
        ## MFL: recon_region_map is a List of ints where each element is the number of neurons in each region (so idx of first region is 0:0th element of this list)
        all_ic_samp = []
        all_ic_std = []
        for region_idx in range(0, len(self.region_readin)):
            region_name = self.hparams.recon_region_name[region_idx]
            recon_region_map = batch[0].recon_region_map[0]
            region_start = 0
            if region_idx > 0:
                region_start = recon_region_map[region_idx-1]
            region_end = recon_region_map[region_idx]
            session_ic_samp = []
            session_ic_std = []
            for s in sessions:
                ic_data = torch.flatten(batch[s].recon_data[:, 0:50, region_start:region_end], start_dim=1) 
                input_layer = self.region_readin[region_idx][s].to(self.device)
                std_layer = self.region_std[region_idx][s].to(self.device)
                ic_mean = input_layer(ic_data)
                ic_std = torch.sqrt(torch.exp(std_layer(ic_data)) + self.hparams.ic_post_var_min)
                ic_post = self.ic_prior[region_idx].make_posterior(ic_mean, ic_std)
                ic_samp = ic_post.rsample() if sample_posteriors else ic_mean
                session_ic_samp.append(ic_samp)
                session_ic_std.append(ic_std)
            all_ic_samp.append(torch.cat(session_ic_samp))
            all_ic_std.append(torch.cat(session_ic_std))
        
        ## MFL annotation: Run decoder
        all_gen_init = []
        all_gen_states = []
        all_con_states = []
        all_co_means = []
        all_co_stds = []
        all_gen_inputs = []
        all_factors = []
        for dIdx in range(0, len(self.decoders)):
            decoder = self.decoders[dIdx].to(self.device)
            ci_samp = all_ic_samp[dIdx].to(self.device)
            # Unroll the decoder to estimate latent states
            (
                gen_init,
                gen_states,
                con_states,
                co_means,
                co_stds,
                gen_inputs,
                factors,
            ) = decoder(ci_samp, ci[dIdx], ext_input, sample_posteriors=sample_posteriors)
            #print(gen_init.shape, gen_states.shape, con_states.shape, co_means.shape, co_stds.shape, gen_inputs.shape, factors.shape)
            all_gen_init.append(gen_init)
            all_gen_states.append(gen_states)
            all_con_states.append(con_states)
            all_co_means.append(co_means)
            all_co_stds.append(co_stds)
            all_gen_inputs.append(gen_inputs)
            all_factors.append(factors)
        ## MFL: Need to concatenate all_* variables along neurons dimension 
        all_gen_init = torch.cat(all_gen_init, dim=-1)
        all_gen_states = torch.cat(all_gen_states, dim=-1)
        all_con_states = torch.cat(all_con_states, dim=-1)
        all_co_means = torch.cat(all_co_means, dim=-1)
        all_co_stds = torch.cat(all_co_stds, dim=-1)
        all_gen_inputs = torch.cat(all_gen_inputs, dim=-1)
        all_factors = torch.cat(all_factors, dim=-1)
        all_ic_samp = torch.cat(all_ic_samp, dim=-1)
        all_ic_std = torch.cat(all_ic_std, dim=-1)
        
        # Convert the factors representation into output distribution parameters
        all_factors = torch.split(all_factors, batch_sizes)
        output_params = [self.readout[s](f) for s, f in zip(sessions, all_factors)]
        
        # Separate parameters of the output distribution
        output_params = [
            self.recon[s].reshape_output_params(op)
            for s, op in zip(sessions, output_params)
        ]
        # Convert the output parameters to means if requested
        if output_means:
            output_params = [
                self.recon[s].compute_means(op)
                for s, op in zip(sessions, output_params)
            ]
        # Separate model outputs by session
        output = transpose_lists(
            [
                output_params,
                all_factors,
                torch.split(all_ic_samp, batch_sizes),
                torch.split(all_ic_std, batch_sizes),
                torch.split(all_co_means, batch_sizes),
                torch.split(all_co_stds, batch_sizes),
                torch.split(all_gen_states, batch_sizes),
                torch.split(all_gen_init, batch_sizes),
                torch.split(all_gen_inputs, batch_sizes),
                torch.split(all_con_states, batch_sizes),
            ]
        )
        # Return the parameter estimates and all intermediate activations
        return {s: SessionOutput(*o) for s, o in zip(sessions, output)}

    def configure_optimizers(self) -> Union[torch.optim.Optimizer, Dict[str, Any]]:
        """
        Configures the optimizers for the model.

        Returns
        -------
        optimizer : torch.optim.AdamW
            The AdamW optimizer with parameters from the hyperparameters.
        scheduler : torch.optim.lr_scheduler.ReduceLROnPlateau
            The learning rate scheduler that reduces the learning rate over time.
            Only returned if `lr_scheduler` in hyperparameters is True.

        """
        hps = self.hparams
        # Create an optimizer
        optimizer = torch.optim.AdamW(
            self.parameters(),
            lr=hps.lr_init,
            betas=(hps.lr_adam_beta1, hps.lr_adam_beta2),
            eps=hps.lr_adam_epsilon,
            weight_decay=hps.weight_decay,
        )
        if hps.lr_scheduler:
            # Create a scheduler to reduce the learning rate over time
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                optimizer=optimizer,
                mode="min",
                factor=hps.lr_decay,
                patience=hps.lr_patience,
                threshold=0.0,
                min_lr=hps.lr_stop,
                verbose=True,
            )
            return {
                "optimizer": optimizer,
                "lr_scheduler": scheduler,
                "monitor": "valid/recon_smth",
            }
        else:
            return optimizer

    def _compute_ramp(self, start: int, increase: int):
        # Compute a coefficient that ramps from 0 to 1 over `increase` epochs
        ramp = (self.current_epoch + 1 - start) / (increase + 1)
        return torch.clamp(torch.tensor(ramp), 0, 1)

    def on_before_optimizer_step(
        self, optimizer: torch.optim.Optimizer, optimizer_idx: int
    ):
        """
        This method is called before each optimizer step to gradually ramp up weight decay.

        Parameters
        ----------
        optimizer : torch.optim.Optimizer
            The optimizer that will be used to update the model's parameters.
        optimizer_idx : int
            The index of the optimizer.
        """
        hps = self.hparams
        # Gradually ramp weight decay alongside the l2 parameters
        l2_ramp = self._compute_ramp(hps.l2_start_epoch, hps.l2_increase_epoch)
        optimizer.param_groups[0]["weight_decay"] = l2_ramp * hps.weight_decay

    def _shared_step(
        self,
        batch: Dict[int, Tuple[SessionBatch, Tuple[torch.Tensor]]],
        batch_idx: int,
        split: Literal["train", "valid"],
    ) -> torch.Tensor:
        hps = self.hparams
        # Check that the split argument is valid
        assert split in ["train", "valid"]
        # Determine which sessions are in the batch
        sessions = sorted(batch.keys())
        # Discard the extra data - only the SessionBatches are relevant here
        batch = {s: b[0] for s, b in batch.items()}
        # Process the batch for each session (in order so aug stack can keep track)
        aug_stack = self.train_aug_stack if split == "train" else self.infer_aug_stack
        batch = {s: aug_stack.process_batch(batch[s]) for s in sessions}
        # Perform the forward pass
        output = self.forward(
            batch, sample_posteriors=hps.variational, output_means=False
        )
        
        # Compute the reconstruction loss
        recon_all = [
            self.recon[s].compute_loss(batch[s].recon_data, output[s].output_params)
            for s in sessions
        ]
        
        # Apply losses processing
        recon_all = [
            aug_stack.process_losses(ra, batch[s], self.log, split)
            for ra, s in zip(recon_all, sessions)
        ]
        # Compute bits per spike
        sess_bps, sess_co_bps, sess_fp_bps = transpose_lists(
            [
                regional_bits_per_spike(
                    output[s].output_params[..., 0],
                    batch[s].recon_data,
                    hps.encod_data_dim,
                    hps.encod_seq_len,
                )
                for s in sessions
            ]
        )
        bps = torch.mean(torch.stack(sess_bps))
        co_bps = torch.mean(torch.stack(sess_co_bps))
        fp_bps = torch.mean(torch.stack(sess_fp_bps))
        # Aggregate the heldout cost for logging
        if not hps.recon_reduce_mean:
            recon_all = [torch.sum(ra, dim=(1, 2)) for ra in recon_all]
        # Compute reconstruction loss for each session
        sess_recon = [ra.mean() for ra in recon_all]
        recon = torch.mean(torch.stack(sess_recon))
        # Compute the L2 penalty on recurrent weights
        l2 = compute_l2_penalty(self, self.hparams)
        # Collect posterior parameters for fast KL calculation
        ic_mean = torch.cat([output[s].ic_mean for s in sessions])
        ic_std = torch.cat([output[s].ic_std for s in sessions])
        co_means = torch.cat([output[s].co_means for s in sessions])
        co_stds = torch.cat([output[s].co_stds for s in sessions])
        
        # Compute the KL penalty on posteriors
        region_units = torch.cat([torch.tensor([0]), torch.cumsum(torch.tensor(self.hparams.recon_data_dim), dim=0)]).to(self.device)
        ic_dims = torch.cat([torch.tensor([0]), torch.cumsum(torch.tensor(self.hparams.ci_enc_dim), dim=0)]).to(self.device)
        co_dims = torch.cat([torch.tensor([0]), torch.cumsum(torch.tensor(self.hparams.co_dim), dim=0)]).to(self.device)
        ic_kl = 0.0
        co_kl = 0.0
        for region_idx in range(0, len(self.hparams.recon_region_name)):
            region_name = self.hparams.recon_region_name[region_idx]
            # region_start = region_units[region_idx]
            # region_stop = region_units[region_idx+1]
            ic_start = ic_dims[region_idx]
            ic_stop = ic_dims[region_idx+1]
            co_start = co_dims[region_idx]
            co_stop = co_dims[region_idx+1]
            ic_prior = self.ic_prior[region_idx].to(self.device)
            kl_ic_scale = getattr(self.hparams, "kl_ic_scale_" + region_name)
            co_prior = self.co_prior[region_idx].to(self.device)
            kl_co_scale = getattr(self.hparams, "kl_co_scale_" + region_name) #[region_idx]
            ic_mean_region = ic_mean[:, ic_start:ic_stop].to(self.device)
            ic_std_region = ic_std[:, ic_start:ic_stop].to(self.device)
            co_mean_region = co_means[:, :, co_start:co_stop].to(self.device)
            co_std_region = co_stds[:, :, co_start:co_stop].to(self.device)
            
            ic_kl_region = ic_prior(ic_mean_region, ic_std_region) * kl_ic_scale
            co_kl_region = co_prior(co_mean_region, co_std_region) * kl_co_scale
            ic_kl += ic_kl_region
            co_kl += co_kl_region
        #ic_kl = self.ic_prior(ic_mean, ic_std) * self.hparams.kl_ic_scale
        #co_kl = self.co_prior(co_means, co_stds) * self.hparams.kl_co_scale
        # Compute ramping coefficients
        l2_ramp = self._compute_ramp(hps.l2_start_epoch, hps.l2_increase_epoch)
        kl_ramp = self._compute_ramp(hps.kl_start_epoch, hps.kl_increase_epoch)
        # Compute the final loss
        loss = hps.loss_scale * (recon + l2_ramp * l2 + kl_ramp * (ic_kl + co_kl))
        # Compute the reconstruction accuracy, if applicable
        if batch[0].truth.numel() > 0:
            output_means = [
                self.recon[s].compute_means(output[s].output_params) for s in sessions
            ]
            r2 = torch.mean(
                torch.stack(
                    [
                        r2_score(om, batch[s].truth)
                        for om, s in zip(output_means, sessions)
                    ]
                )
            )
        else:
            r2 = float("nan")
        # Compute batch sizes for logging
        batch_sizes = [len(batch[s].encod_data) for s in sessions]
        # Log per-session metrics
        for s, recon_value, batch_size in zip(sessions, sess_recon, batch_sizes):
            self.log(
                name=f"{split}/recon/sess{s}",
                value=recon_value,
                on_step=False,
                on_epoch=True,
                batch_size=batch_size,
            )
        # Collect metrics for logging
        metrics = {
            f"{split}/loss": loss,
            f"{split}/recon": recon,
            f"{split}/bps": max(bps, -1.0),
            f"{split}/co_bps": max(co_bps, -1.0),
            f"{split}/fp_bps": max(fp_bps, -1.0),
            f"{split}/r2": r2,
            f"{split}/wt_l2": l2,
            f"{split}/wt_l2/ramp": l2_ramp,
            f"{split}/wt_kl": ic_kl + co_kl,
            f"{split}/wt_kl/ic": ic_kl,
            f"{split}/wt_kl/co": co_kl,
            f"{split}/wt_kl/ramp": kl_ramp,
        }
        if split == "valid":
            # Update the smoothed reconstruction loss
            self.valid_recon_smth.update(recon, batch_size)
            # Add validation-only metrics
            metrics.update(
                {
                    "valid/recon_smth": self.valid_recon_smth,
                    "hp_metric": recon,
                    "cur_epoch": float(self.current_epoch),
                }
            )
        # Log overall metrics
        self.log_dict(
            metrics,
            on_step=False,
            on_epoch=True,
            batch_size=sum(batch_sizes),
        )

        return loss

    def training_step(
        self, batch: Dict[int, Tuple[SessionBatch, Tuple[torch.Tensor]]], batch_idx: int
    ) -> torch.Tensor:
        """
        Performs a training step.

        Parameters
        ----------
        batch : Dict[int, Tuple[SessionBatch, Tuple[torch.Tensor]]]
            The batch of data to be processed. The dictionary keys are session IDs, and the values are tuples
            containing a SessionBatch object and a tuple of torch tensors.
        batch_idx : int
            The index of the current batch.

        Returns
        -------
        torch.Tensor
            The loss for the current training step.
        """
        return self._shared_step(batch, batch_idx, "train")

    def validation_step(
        self, batch: Dict[int, Tuple[SessionBatch, Tuple[torch.Tensor]]], batch_idx: int
    ) -> torch.Tensor:
        """
        Performs a validation step.

        Parameters
        ----------
        batch : Dict[int, Tuple[SessionBatch, Tuple[torch.Tensor]]]
            The batch of data to be processed. The dictionary keys are session IDs, and the values are tuples
            containing a SessionBatch object and a tuple of torch tensors.
        batch_idx : int
            The index of the current batch.

        Returns
        -------
        torch.Tensor
            The loss for the current validation step.
        """
        return self._shared_step(batch, batch_idx, "valid")

    def predict_step(
        self,
        batch: Dict[int, Tuple[SessionBatch, Tuple[torch.Tensor]]],
        batch_idx: int,
        sample_posteriors=True,
    ) -> Dict[int, SessionOutput]:
        """
        Performs a prediction step.

        Parameters
        ----------
        batch : Dict[int, Tuple[SessionBatch, Tuple[torch.Tensor]]]
            The batch of data to be processed. The dictionary keys are session IDs, and the values are tuples
            containing a SessionBatch object and a tuple of torch tensors.
        batch_idx : int
            The index of the current batch.
        sample_posteriors : bool, optional
            Whether to sample from the posterior distribution or pass means, by default True

        Returns
        -------
        Dict[int, SessionOutput]
            The output of the forward pass through the model.
        """
        # Discard the extra data - only the SessionBatches are relevant here
        batch = {s: b[0] for s, b in batch.items()}
        # Process the batch for each session
        batch = {s: self.infer_aug_stack.process_batch(b) for s, b in batch.items()}
        # Reset to clear any saved masks
        self.infer_aug_stack.reset()
        # Perform the forward pass
        return self.forward(
            batch=batch,
            sample_posteriors=self.hparams.variational and sample_posteriors,
            output_means=True,
        )

    def on_validation_epoch_end(self):
        """
        Logs hyperparameters that may change during PBT.
        """
        # Log hyperparameters that may change during PBT
        hp_dict = {
            "hp/lr_init": self.hparams.lr_init,
            "hp/dropout_rate": self.hparams.dropout_rate,
            "hp/l2_ic_enc_scale": self.hparams.l2_ic_enc_scale,
            #"hp/l2_ci_enc_scale": self.hparams.l2_ci_enc_scale,
            #"hp/l2_gen_scale": self.hparams.l2_gen_scale,
            #"hp/l2_con_scale": self.hparams.l2_con_scale,
            #"hp/kl_co_scale": self.hparams.kl_co_scale,
            #"hp/kl_ic_scale": self.hparams.kl_ic_scale,
            "hp/weight_decay": self.hparams.weight_decay,
            }
            
        for region_idx in range(0, len(self.hparams.recon_region_name)):
            region_name = self.hparams.recon_region_name[region_idx]
            l2_ci_enc_scale_region = self.hparams.l2_ci_enc_scale[region_idx]
            l2_gen_scale_region = self.hparams.l2_gen_scale[region_idx]
            l2_con_scale_region = self.hparams.l2_con_scale[region_idx]
            kl_co_scale_region = self.hparams.kl_co_scale[region_idx]
            kl_ic_scale_region = self.hparams.kl_ic_scale[region_idx]
            hp_dict["hp/l2_ci_enc_scale_ " + region_name] = l2_ci_enc_scale_region
            hp_dict["hp/l2_gen_scale_" + region_name] = l2_gen_scale_region
            hp_dict["hp/l2_con_scale_" + region_name] = l2_con_scale_region
            hp_dict["hp/kl_co_scale_" + region_name] = kl_co_scale_region
            hp_dict["hp/kl_ic_scale_" + region_name] = kl_ic_scale_region
        
        self.log_dict(hp_dict)

        # Log CD rate if CD is being used
        for aug in self.train_aug_stack.batch_transforms:
            if hasattr(aug, "cd_rate"):
                self.log("hp/cd_rate", aug.cd_rate)
