# ~/.bash_profile: executed by bash login shells.

if [ "$BASH" ]; then
  if [ -f ~/.bashrc ]; then
    . ~/.bashrc
  fi
fi

mesg n

# Set up SpiNNaker toolchain
[[ -f ~/.spinnaker_env ]] &&  . ~/.spinnaker_env
